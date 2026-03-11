"""Main CircuitPython code that collects data from the I2C sensors and prints to serial."""

import time
import asyncio
import board
import busio

import adafruit_scd4x
import adafruit_sht4x
import adafruit_sgp40
import adafruit_sgp41
from adafruit_pm25.i2c import PM25_I2C
from adafruit_pcf8523.pcf8523 import PCF8523

from led import LED
from button import Button
from sd_logger import SDLogger
from utils import format_value, format_rtc_datetime, calculate_dew_point, calculate_air_score

class AirQuality:

    def __init__(self, led, button, logger):
        """Initialize the AirQuality class with LED, button, and logger."""
        self.led = led
        self.button = button
        self.sd_logger = logger

        # Initialize I2C (and wait until ready)
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)
        while not self.i2c.try_lock():
            pass
        self.i2c.unlock()

        # Initialize sensors
        self.co2_sensor = adafruit_scd4x.SCD4X(self.i2c) # CO2 / T / RH: SCD4x
        self.co2_sensor.start_periodic_measurement()
        self.temp_humidity_sensor = adafruit_sht4x.SHT4x(self.i2c) # Temp / RH: SHT4x
        self.voc_sensor = adafruit_sgp40.SGP40(self.i2c) # VOC: SGP40
        self.pm_sensor = PM25_I2C(self.i2c, reset_pin=None) # PM: PMSA003I via adafruit_pm25 (I2C)
        self.rtc = PCF8523(self.i2c) # RTC: PCF8523 (RTC)

        # Warmup tracking (SGP40 & SCD4x like a little time)
        self.start_time = self.rtc.datetime

        self.logging = False
        self._shutdown = False  # Flag to indicate if a safe shutdown has been initiated

        # Initialize sensor values
        self.co2_value = None
        self.temp_value = None
        self.dew_point = None
        self.humidity_value = None
        self.voc_raw = None
        self.voc_index = None
        self.pm = None

        # Initialize intervals for reading sensors and logging
        self.voc_index_interval = 1.0  # seconds
        self.sensor_interval = 5.0  # seconds
        self.print_interval = 5.0  # seconds
        self.log_interval = 5.0  # seconds

        # Log system initialization
        print("System initialized and ready.")
        self.sd_logger.log_info(self.rtc.datetime, "System initialized and ready.")
        self.led.blink_once('magenta')  # Indicate system is ready

    def safe_shutdown(self):
        """Perform safe shutdown actions: log, LED, and optionally power down hardware."""
        msg = "Safe shutdown initiated."
        print(msg)
        self.sd_logger.log_info(self.rtc.datetime, msg)
        self.sd_logger.unmount()
        self._shutdown = True  # Set shutdown flag
        self.led.blink_once('yellow')

    async def read_sensors(self):
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
                msg = f"Error reading CO2 sensor: {e}"
                print(msg)
                self.led.blink_once('red')
                self.sd_logger.log_info(self.rtc.datetime, msg)

            try:
                # SHT4x temp / RH
                self.temp_value = self.temp_humidity_sensor.temperature
                self.humidity_value = self.temp_humidity_sensor.relative_humidity
                # Calculate dew point
                self.dew_point = calculate_dew_point(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.temp_value = None
                self.humidity_value = None
                msg = f"Error reading temperature/humidity sensor: {e}"
                print(msg)
                self.led.blink_once('red')
                self.sd_logger.log_info(self.rtc.datetime, msg)

            try:
                # SGP40 raw VOC reading
                self.voc_raw = self.voc_sensor.measure_raw(self.temp_value, self.humidity_value)
            except (OSError, RuntimeError) as e:
                self.voc_raw = None
                msg = f"Error reading VOC sensor: {e}"
                print(msg)
                self.led.blink_once('red')
                self.sd_logger.log_info(self.rtc.datetime, msg)

            try:
                # PM25 dict
                self.pm = self.pm_sensor.read()
            except (OSError, RuntimeError) as e:
                self.pm = None
                msg = f"Error reading PM sensor: {e}"
                print(msg)
                self.led.blink_once('red')
                self.sd_logger.log_info(self.rtc.datetime, msg)

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


    async def read_voc_index(self):
        while not self._shutdown:
            try:
                self.voc_index = self.voc_sensor.measure_index()
            except (OSError, RuntimeError) as e:
                msg = f"Error reading VOC index: {e}"
                print(msg)
                self.led.blink_once('red')
                self.sd_logger.log_info(self.rtc.datetime, msg)
                self.voc_index = None
            await asyncio.sleep(self.voc_index_interval)


    async def print_data(self):
        while not self._shutdown:

            print(
                "RTC: {} | T: {} C RH: {}% -> DP: {} | CO2: {} ppm | VOC Raw: {} VOC Index: {} | PM10: {} PM2.5: {} PM1.0: {}".format(
                    format_rtc_datetime(self.rtc.datetime),
                    format_value(self.temp_value, 2),
                    format_value(self.humidity_value, 2),
                    format_value(self.dew_point, 2),
                    format_value(self.co2_value),
                    format_value(self.voc_raw),
                    format_value(self.voc_index),
                    format_value(self.pm10),
                    format_value(self.pm25),
                    format_value(self.pm100),
                )
            )

            if not self.logging:
                air_score = calculate_air_score(self.co2_value, self.temp_value,
                                                self.humidity_value, self.voc_index, self.pm)
                self.led.set_color_by_score(air_score)

            await asyncio.sleep(self.print_interval)  # Wait for the next logging interval

    async def log_data(self):
        while not self._shutdown:
            if self.logging:
                self.sd_logger.log_data_to_sd(format_rtc_datetime(self.rtc.datetime),
                                                self.co2_value, self.temp_value,
                                                self.humidity_value, self.voc_raw,
                                                self.voc_index, self.pm)
                self.led.blink_once('blue')

            await asyncio.sleep(self.log_interval)  # Wait for the next logging interval

    async def monitor_button(self):
        while not self._shutdown:
            self.button.update()  # Update button state
            held_duration = self.button.held()

            # Logging toggle only if not holding for shutdown
            if (held_duration < 2.0) and (held_duration > 0.0):
                self.logging = not self.logging
                if self.logging:
                    # Start new log file with RTC datetime
                    self.sd_logger.start_new_log(self.rtc.datetime)
                    print("Logging started.")
                    self.sd_logger.log_info(self.rtc.datetime, "Logging started.")
                else:
                    self.sd_logger.stop_log()
                    print("Logging stopped.")
                    self.sd_logger.log_info(self.rtc.datetime, "Logging stopped.")
                self.led.blink_once('blue')

            # Safe shutdown only if held
            elif held_duration >= 2.0:
                self.safe_shutdown()

            await asyncio.sleep(0.01)

    async def run(self):
        await asyncio.gather(
            self.read_sensors(),
            self.read_voc_index(),
            self.print_data(),
            self.log_data(),
            self.monitor_button(),
        )


if __name__ == "__main__":
    # --- Init objects ---
    led = LED()
    button = Button()

    try:
        sd_logger = SDLogger()
        air_quality = AirQuality(led, button, sd_logger)

        try:
            asyncio.run(air_quality.run())

        except KeyboardInterrupt:
            print("Program interrupted by user.")
            sd_logger.log_info(air_quality.rtc.datetime, "Program interrupted by user.")
            air_quality.safe_shutdown()

        except Exception as e:
            print(f'Error: {e}')
            sd_logger.log_info(air_quality.rtc.datetime, f"Error: {e}")
            air_quality.safe_shutdown()
            led.error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.error_blink()
