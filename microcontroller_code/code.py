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
from utils import format_value, calculate_air_score

class AirQuality:
    """Collects data from sensors and prints to the serial port."""

    def __init__(self, led, button, logger):

        """Initialize the AirQuality class with LED, button, and logger."""
        self.led = led
        self.button = button
        self.sd_logger = sd_logger

        # Initialize I2C (and wait until ready)
        self.i2c = busio.I2C(board.SCL, board.SDA)
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
        self.start_time = time.monotonic()

        self.logging = False

        self.led.blink_once('white')  # Indicate system is ready

    async def run(self):
        sensor_interval = 5  # seconds
        last_sensor_time = self.rtc.datetime
        while True:
            # Check button frequently
            if self.button.pressed():
                self.logging = not self.logging
                print(f"Logging {'started' if self.logging else 'stopped'}.")
                self.led.blink_once('blue')

            now = self.rtc.datetime
            if (now - last_sensor_time).total_seconds() >= sensor_interval:
                # Reinitialize values as None each loop to handle sensor read failures gracefully
                co2_value = None
                temp_value = None
                humidity_value = None
                voc_raw = None
                pm = None

                # SCD4x CO2
                if self.co2_sensor.data_ready:
                    co2_value = self.co2_sensor.CO2

                # SHT4x temp / RH
                temp_value = self.temp_humidity_sensor.temperature
                humidity_value = self.temp_humidity_sensor.relative_humidity

                # SGP40 raw VOC reading
                voc_raw = self.voc_sensor.measure_raw(temp_value, humidity_value)

                # PM25 dict
                pm = self.pm_sensor.read()

                # Extract relevant PM values
                pm10 = pm.get("pm10 env")
                pm25 = pm.get("pm25 env")
                pm100 = pm.get("pm100 env")

                print(
                    "CO2: {} ppm | SHT  T: {} C RH: {}% | VOC Index: {} | PM: PM10: {}, PM2.5: {}, PM1.0: {}".format(
                        format_value(co2_value),
                        format_value(temp_value, 2),
                        format_value(humidity_value, 2),
                        format_value(voc_raw),
                        format_value(pm10),
                        format_value(pm25),
                        format_value(pm100),
                    )
                )

                air_score = calculate_air_score(co2_value, temp_value, humidity_value, voc_raw, pm)
                self.led.set_color_by_score(air_score)

                # If logging, log data to SD card (placeholder)
                if self.logging:
                    self.sd_logger.log_data_to_sd(now, co2_value, temp_value, humidity_value, voc_raw, pm)
                    # Blink LED once to indicate logging
                    self.led.blink_once('blue')

                last_sensor_time = now

            await asyncio.sleep(0.01)  # Yield to event loop, check button frequently


if __name__ == "__main__":
    # --- NeoPixel setup ---
    led = LED()
    button = Button()

    try:
        sd_logger = SDLogger()
        air_quality = AirQuality(led, button, sd_logger)
        asyncio.run(air_quality.run())

    except Exception as e:
        print(f'Error: {e}')
        led.error_blink()

