"""Main CircuitPython code that collects data from the I2C sensors and prints to serial."""

import asyncio

import adafruit_scd4x # type: ignore
import adafruit_sht4x # type: ignore
import adafruit_sgp40 # type: ignore
import adafruit_sgp41 # type: ignore
from adafruit_pm25.i2c import PM25_I2C # type: ignore

from sd_logger import SDLogger
from rtc import RTC
from button import Button
from i2c import I2C
from utils import format_value, calculate_dew_point, calculate_air_score_color

class AirQualitySensor:
    """
    AirQuality class that takes sensor measurements and handles all high level processes.
    """

    def __init__(self, led) -> None:
        # Initialize the AirQuality class with button, RTC, and logger
        i2c = I2C()
        self.button = Button()
        self.sd_logger = SDLogger(i2c, led)

        # Initialize sensors
        self.co2_sensor = adafruit_scd4x.SCD4X(i2c) # CO2 / T / RH: SCD4x
        self.co2_sensor.start_periodic_measurement()
        self.temp_humidity_sensor = adafruit_sht4x.SHT4x(i2c) # Temp / RH: SHT4x
        self.voc_sensor = adafruit_sgp40.SGP40(i2c) # VOC: SGP40
        self.pm_sensor = PM25_I2C(i2c, reset_pin=None) # PM: PMSA003I via adafruit_pm25 (I2C)

        # Initialize sensor values
        self.co2_value: int|None = None
        self.temp_value: float|None = None
        self.dew_point: float|None = None
        self.humidity_value: float|None = None
        self.voc_raw: int|None = None
        self.voc_index: int|None = None
        self.pm: dict|None = None

        # Initialize intervals for reading sensors and logging
        self.voc_index_interval: float = 1.0  # seconds
        self.sensor_interval: float = 5.0  # seconds
        self.print_interval: float = 5.0  # seconds
        self.log_interval: float = 5.0  # seconds

        # Flags
        self._logging: bool = False
        self._shutdown: bool = False

        # Indicate initialization is complete and system is ready
        self.sd_logger.log_info(msg="System initialized and ready.", color='magenta')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.safe_shutdown()


    def safe_shutdown(self) -> None:
        """Perform safe shutdown actions: log, LED, and optionally power down hardware."""
        self.sd_logger.log_info("Safe shutdown initiated.")
        self.sd_logger.unmount()
        self._shutdown = True  # Set shutdown flag

    async def read_sensors(self) -> None:
        """
        Reads all connected air quality sensors, handling I2C and runtime errors gracefully.
        Returns:
            tuple: (self.co2_value, self.temp_value, humidity_value, self.voc_raw, pm)
                self.co2_value (float or None): CO2 concentration in ppm, or None if read failed
                self.temp_value (float or None): Temperature in Celsius, or None if read failed
                humidity_value (float or None): Relative humidity in %, or None if read failed
                self.voc_raw (int or None): Raw VOC sensor value, or None if read failed
                pm (dict or None): PM sensor readings dictionary, or None if read failed
        """

        while not self._shutdown:
            try:
                # SCD4x CO2
                if self.co2_sensor.data_ready:
                    self.co2_value = self.co2_sensor.CO2
            except (OSError, RuntimeError) as e:
                self.co2_value = None
                self.sd_logger.log_info(msg=f"Error reading CO2 sensor: {e}", color='red')

            try:
                # SHT4x temp / RH
                self.temp_value = self.temp_humidity_sensor.temperature
                self.humidity_value = self.temp_humidity_sensor.relative_humidity
                # Calculate dew point
                self.dew_point = calculate_dew_point(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.temp_value = None
                self.humidity_value = None
                self.sd_logger.log_info(msg=f"Error reading temperature/humidity sensor: {e}", color='red')

            try:
                # SGP40 raw VOC reading
                self.voc_raw = self.voc_sensor.measure_raw(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.voc_raw = None
                self.sd_logger.log_info(msg=f"Error reading VOC sensor: {e}", color='red')

            try:
                # PM25 dict
                self.pm = self.pm_sensor.read()
            except (OSError, RuntimeError) as e:
                self.pm = None
                self.sd_logger.log_info(msg=f"Error reading PM sensor: {e}", color='red')

            # Extract relevant PM values
            if self.pm:
                self.pm10 = self.pm.get("pm10 env")
                self.pm25 = self.pm.get("pm25 env")
                self.pm100 = self.pm.get("pm100 env")
            else:
                self.pm10 = None
                self.pm25 = None
                self.pm100 = None

            await asyncio.sleep(self.sensor_interval)  # Yield to event loop, check button frequently


    async def read_voc_index(self) -> None:
        """
        Reads voc index from voc sensor.
        Returns self.voc_index (int or None): Calculated VOC Index, or None if read failed
        """
        while not self._shutdown:
            try:
                self.voc_index = self.voc_sensor.measure_index(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.voc_index = None
                self.sd_logger.log_info(msg=f"Error reading VOC index: {e}", color='red')
            await asyncio.sleep(self.voc_index_interval)


    async def print_data(self) -> None:
        """
        Prints sensor data to console and calculates air score and sets led color by score if not logging.
        """
        while not self._shutdown:
            msg = ("T: {} C RH: {}% -> DP: {} | CO2: {} ppm | VOC Raw: {} VOC Index: {} | PM10: {} PM2.5: {} PM1.0: {}".format(
                        format_value(self.temp_value, 2),
                        format_value(self.humidity_value, 2),
                        format_value(self.dew_point, 2),
                        format_value(self.co2_value),
                        format_value(self.voc_raw),
                        format_value(self.voc_index),
                        format_value(self.pm100),
                        format_value(self.pm25),
                        format_value(self.pm10),
            ))

            self.sd_logger.print_with_timestamp(msg)

            if not self._logging:
                air_score_color = calculate_air_score_color(self.co2_value, self.temp_value,
                                                self.humidity_value, self.voc_index, self.pm25)

                self.sd_logger.led.set_color(air_score_color)

        await asyncio.sleep(self.print_interval)  # Wait for the next logging interval

    async def log_data(self) -> None:
        """
        Logs data if self._logging is True.
        """
        while not self._shutdown:
            if self._logging:
                self.sd_logger.log_data(self.co2_value, self.temp_value,
                                        self.humidity_value, self.voc_raw,
                                        self.voc_index, self.pm)

            await asyncio.sleep(self.log_interval)  # Wait for the next logging interval

    async def monitor_button(self) -> None:
        """
        Monitors button for short press (starts logging) or long press (initiates safe shutdown).
        """
        while not self._shutdown:
            self.button.update()  # Update button state
            held_duration = self.button.held()

            # Logging toggle only if not holding for shutdown
            if (held_duration < 2.0) and (held_duration > 0.0):
                self._logging = not self._logging
                if self._logging:
                    # Start new log file with RTC datetime
                    self.sd_logger.start_new_log()
                    self.sd_logger.log_info(msg="Logging started.", color='blue')
                else:
                    self.sd_logger.stop_log()
                    self.sd_logger.log_info(msg="Logging stopped.", color='blue')

            # Safe shutdown only if held
            elif held_duration >= 2.0:
                raise KeyboardInterrupt("Button held for safe shutdown.")

            await asyncio.sleep(0.01)

    async def run(self) -> None:
        """
        Main function that runs all async functions concurrently.
        """
        await asyncio.gather(
            self.read_sensors(),
            self.read_voc_index(),
            self.print_data(),
            self.log_data(),
            self.monitor_button(),
        )
