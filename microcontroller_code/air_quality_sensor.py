"""Main CircuitPython code that collects data from the I2C sensors and prints to serial."""

import asyncio

from adafruit_scd4x import SCD4X # type: ignore
from adafruit_sht4x import SHT4x # type: ignore
from adafruit_sgp41.sgp41 import SGP41 # type: ignore
from adafruit_pm25.i2c import PM25_I2C # type: ignore

from utils import calculate_dew_point, get_display_data
from aqs_data import AQSData

class AirQualitySensor:
    """
    AirQuality class that takes sensor measurements and handles all high level processes.
    """

    def __init__(self, led, i2c, data_logger, event_logger, button, clock, cfg) -> None:
        # Load settings from TOML
        self.cfg = cfg

        # Initialize the AirQuality class with button, RTC, and logger
        self.i2c = i2c
        self.led = led
        self.data_logger = data_logger
        self.event_logger = event_logger
        self.button = button
        self.clock = clock

        # Sync the internal clock with the hardware RTC and check battery status
        self.clock.sync()
        if self.clock.battery_low:
            self.event_logger.warning(msg="RTC battery is low.")

        # Initialize sensors
        self.co2_sensor = SCD4X(i2c) # CO2 / T / RH: SCD4x
        self.co2_sensor.start_periodic_measurement()
        self.temp_humidity_sensor = SHT4x(i2c) # Temp / RH: SHT4x
        self.gas_sensor = SGP41(i2c) # VOC/NOx: SGP41
        self.pm_sensor = PM25_I2C(i2c, reset_pin=None) # PM: PMSA003I via adafruit_pm25 (I2C)

        # Initialize sensor values
        self.co2_value: int|None = None
        self.temp_value: float|None = None
        self.dew_point: float|None = None
        self.humidity_value: float|None = None
        self.voc_raw: int|None = None
        self.voc_index: int|None = None
        self.nox_raw: int|None = None
        self.nox_index: int|None = None
        self.pm10: float|None = None
        self.pm25: float|None = None
        self.pm100: float|None = None

        # Settings
        self.shutdown_hold = cfg.get("button.shutdown_hold", 2.0)

        # Initialize intervals from settings
        self.voc_index_interval: float = cfg.get("sensor.voc_index_interval", 1.0)
        self.sensor_interval: float = cfg.get("sensor.sensor_interval", 5.0)
        self.print_interval: float = cfg.get("sensor.print_interval", 5.0)
        self.log_interval: float = cfg.get("sensor.log_interval", 5.0)

        # Flags
        self._logging: bool = False
        self._shutdown: bool = False

        # Indicate initialization is complete and system is ready
        self.event_logger.debug(msg="System initialized and ready.")
        self.led.startup_blink()


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.safe_shutdown()


    def safe_shutdown(self) -> None:
        """Perform safe shutdown actions: log, LED, and optionally power down hardware."""
        self.event_logger.debug("Safe shutdown initiated.")
        self.data_logger.shutdown()  # Ensure all sinks are closed
        self._shutdown = True  # Set shutdown flag
        self.led.shutdown_blink()
    

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
                self.event_logger.error(msg=f"Error reading CO2 sensor: {e}")

            try:
                # SHT4x temp / RH
                self.temp_value = self.temp_humidity_sensor.temperature
                self.humidity_value = self.temp_humidity_sensor.relative_humidity
                # Calculate dew point
                self.dew_point = calculate_dew_point(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.temp_value = None
                self.humidity_value = None
                self.event_logger.error(msg=f"Error reading temperature/humidity sensor: {e}")

            try:
                # SGP41 raw VOC & NOx reading
                self.voc_raw, self.nox_raw = self.gas_sensor.measure_raw(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.voc_raw = None
                self.nox_raw = None
                self.event_logger.error(msg=f"Error reading VOC/NOx sensor: {e}")

            try:
                # PM25 dict
                pm = self.pm_sensor.read()
            except (OSError, RuntimeError) as e:
                pm = None
                self.event_logger.error(msg=f"Error reading PM sensor: {e}")

            # Extract relevant PM values
            if pm:
                self.pm10 = pm.get("pm10 env")
                self.pm25 = pm.get("pm25 env")
                self.pm100 = pm.get("pm100 env")
            else:
                self.pm10 = None
                self.pm25 = None
                self.pm100 = None

            await asyncio.sleep(self.sensor_interval)  # Yield to event loop, check button frequently


    async def read_voc_nox_index(self) -> None:
        """
        Reads voc and nox indices from gas sensor.
        Returns self.voc_index (int or None): Calculated VOC Index, or None if read failed
        Returns self.nox_index (int or None): Calculated NOx Index, or None if read failed
        """
        while not self._shutdown:
            try:
                self.voc_index, self.nox_index = self.gas_sensor.measure_index(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.voc_index = None
                self.nox_index = None
                self.event_logger.error(msg=f"Error reading VOC/NOx indices: {e}")
            await asyncio.sleep(self.voc_index_interval)


    async def display_data(self) -> None:
        aqs_data = AQSData.from_sensor(self)

        if not self._logging:
            air_score_dict = get_display_data(aqs_data)

            self.led.show_air_quality_data(air_score_dict)

        await asyncio.sleep(self.sensor_interval)  # Wait for the next logging interval


    async def send_data(self) -> None:

        while not self._shutdown:
            aqs_data = AQSData.from_sensor(self)
            self.data_logger.send_data(aqs_data)

            await asyncio.sleep(self.print_interval)  # Wait for the next logging interval


    async def log_data(self) -> None:
        """
        Logs data if self._logging is True.
        """

        while not self._shutdown:
            if self._logging:
                aqs_data = AQSData.from_sensor(self)
                self.data_logger.log_data(aqs_data)

            await asyncio.sleep(self.log_interval)  # Wait for the next logging interval


    async def monitor_button(self) -> None:
        """
        Monitors button for short press (starts logging) or long press (initiates safe shutdown).
        """
        while not self._shutdown:
            self.button.update()  # Update button state

            # Logging toggle only if not holding for shutdown
            if self.button.shutdown_press():
                raise KeyboardInterrupt("Button held for safe shutdown.")

            if self.button.logging_press():
                self._logging = not self._logging
                if self._logging:
                    # Start new log file with RTC datetime
                    self.data_logger.start_new_log()
                    self.event_logger.debug(msg="Logging started.")
                else:
                    self.data_logger.stop_log()
                    self.event_logger.debug(msg="Logging stopped.")

            await asyncio.sleep(0.01)


    async def sync_clock(self) -> None:
        """
        Periodically syncs the system clock with the RTC to ensure accurate timestamps.
        """
        while not self._shutdown:
            try:
                self.clock.sync()
                self.event_logger.debug(msg="System clock synced with RTC.")
            except Exception as e:
                self.event_logger.error(msg=f"Error syncing system clock: {e}")

            await asyncio.sleep(60*60*24)  # Sync every 24 hours


    async def run(self) -> None:
        """
        Main function that runs all async functions concurrently.
        """
        await asyncio.gather(
            self.read_sensors(),
            self.read_voc_nox_index(),
            self.display_data(),
            self.send_data(),
            self.log_data(),
            self.monitor_button(),
            self.sync_clock()  
        )
