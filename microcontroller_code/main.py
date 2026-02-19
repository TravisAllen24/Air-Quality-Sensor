"""Main CircuitPython code that collects data from the I2C sensors and prints to serial."""

import time
import board
import busio

import adafruit_scd4x
import adafruit_sht4x
import adafruit_sgp40
from adafruit_pm25.i2c import PM25_I2C

from led import LED
from utils import format_value, calculate_air_score

class AirQuality:
    """Collects data from sensors and prints to the serial port."""

    def __init__(self):
        # --- NeoPixel setup ---
        self.led = LED(board.NEOPIXEL, brightness=0.2)

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

        # Warmup tracking (SGP40 & SCD4x like a little time)
        self.start_time = time.monotonic()

    def run(self):
        while True:
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
            pm10 = pm.get("pm10 standard")
            pm25 = pm.get("pm25 standard")
            pm100 = pm.get("pm100 standard")

            print(
                "CO2: {} ppm | SHT  T: {} C RH: {}% | VOC: {} | PM: PM10: {}, PM2.5: {}, PM1.0: {}".format(
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
            time.sleep(5)


if __name__ == "__main__":
    AirQuality().run()

