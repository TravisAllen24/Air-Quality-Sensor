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
from utils import format_value, format_rtc_datetime, calculate_air_score

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

        # CO2 / T / RH: SCD4x
        self.co2_sensor = adafruit_scd4x.SCD4X(self.i2c)
        self.co2_sensor.start_periodic_measurement()

        # Temp / RH: SHT4x
        self.temp_humidity_sensor = adafruit_sht4x.SHT4x(self.i2c)

        # VOC: SGP40
        self.voc_sensor = adafruit_sgp40.SGP40(self.i2c)

        # PM: PMSA003I via adafruit_pm25 (I2C)
        self.pm_sensor = PM25_I2C(self.i2c, reset_pin=None)

        # RTC: PCF8523 (RTC)
        self.rtc = PCF8523(self.i2c)

        # Warmup tracking (SGP40 & SCD4x like a little time)
        self.start_time = self.rtc.datetime

        self.logging = False
        self._shutdown = False  # Flag to indicate if a safe shutdown has been initiated

        self.sd_logger.log_info(self.rtc.datetime, "System initialized and ready.")

        self.led.blink_once('magenta')  # Indicate system is ready

    def safe_shutdown(self):
        """Perform safe shutdown actions: log, LED, and optionally power down hardware."""
        msg = "Safe shutdown initiated."
        print(msg)
        self.sd_logger.log_info(self.rtc.datetime, msg)
        self.sd_logger.unmount()
        self.led.blink_once('yellow')
        self._shutdown = True  # Set shutdown flag
        time.sleep(1)  # Allow time for LED blink before turning off

    def read_all_sensors(self):
        """
        Reads all connected air quality sensors, handling I2C and runtime errors gracefully.
        Returns:
            tuple: (co2_value, temp_value, humidity_value, voc_raw, pm)
                co2_value (float or None): CO2 concentration in ppm, or None if read failed
                temp_value (float or None): Temperature in Celsius, or None if read failed
                humidity_value (float or None): Relative humidity in %, or None if read failed
                voc_raw (int or None): Raw VOC sensor value, or None if read failed
                pm (dict or None): PM sensor readings dictionary, or None if read failed
        """
        co2_value = None
        temp_value = None
        humidity_value = None
        voc_raw = None
        voc_index = None
        pm = None

        try:
            # SCD4x CO2
            if self.co2_sensor.data_ready:
                co2_value = self.co2_sensor.CO2
        except (OSError, RuntimeError) as e:
            msg = f"Error reading CO2 sensor: {e}"
            print(msg)
            self.led.blink_once('red')
            self.sd_logger.log_info(self.rtc.datetime, msg)

        try:
            # SHT4x temp / RH
            temp_value = self.temp_humidity_sensor.temperature
            humidity_value = self.temp_humidity_sensor.relative_humidity
        except (OSError, RuntimeError) as e:
            msg = f"Error reading temperature/humidity sensor: {e}"
            print(msg)
            self.led.blink_once('red')
            self.sd_logger.log_info(self.rtc.datetime, msg)

        try:
            # SGP40 raw VOC reading
            voc_raw = self.voc_sensor.measure_raw(temp_value, humidity_value)
            voc_index = self.voc_sensor.measure_index(temp_value, humidity_value)
        except (OSError, RuntimeError) as e:
            msg = f"Error reading VOC sensor: {e}"
            print(msg)
            self.led.blink_once('red')
            self.sd_logger.log_info(self.rtc.datetime, msg)

        try:
            # PM25 dict
            pm = self.pm_sensor.read()
        except (OSError, RuntimeError) as e:
            msg = f"Error reading PM sensor: {e}"
            print(msg)
            self.led.blink_once('red')
            self.sd_logger.log_info(self.rtc.datetime, msg)

        return co2_value, temp_value, humidity_value, voc_raw, voc_index, pm


    async def run(self):
        sensor_interval = 5  # seconds
        last_sensor_time = self.rtc.datetime


        while True:
            button.update()  # Update button state
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

            if self._shutdown:
                break  # Exit the loop if a safe shutdown has been initiated

            # ...existing code...

            # Always update now and timestamps for interval check
            now = self.rtc.datetime
            now_ts = time.mktime(now)
            last_sensor_ts = time.mktime(last_sensor_time)

            if (now_ts - last_sensor_ts) >= sensor_interval:
                # Read all sensors and handle errors gracefully
                co2_value, temp_value, humidity_value, voc_raw, voc_index, pm = self.read_all_sensors()

                # Extract relevant PM values
                if pm:
                    pm10 = pm.get("pm10 env")
                    pm25 = pm.get("pm25 env")
                    pm100 = pm.get("pm100 env")
                else:
                    pm10 = None
                    pm25 = None
                    pm100 = None

                print(
                    "RTC: {} | CO2: {} ppm | T: {} C RH: {}% | VOC Raw: {} | VOC Index: {} | PM: PM10: {}, PM2.5: {}, PM1.0: {}".format(
                        format_rtc_datetime(now),
                        format_value(co2_value),
                        format_value(temp_value, 2),
                        format_value(humidity_value, 2),
                        format_value(voc_raw),
                        format_value(voc_index),
                        format_value(pm10),
                        format_value(pm25),
                        format_value(pm100),
                    )
                )

                # If logging, log data to SD card
                if self.logging:
                    self.sd_logger.log_data_to_sd(format_rtc_datetime(now), co2_value, temp_value, humidity_value, voc_raw, voc_index, pm)
                    self.led.blink_once('blue')

                else:
                    air_score = calculate_air_score(co2_value, temp_value, humidity_value, voc_index, pm)
                    self.led.set_color_by_score(air_score)

                last_sensor_time = now

            await asyncio.sleep(0.01)  # Yield to event loop, check button frequently


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
