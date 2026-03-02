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

from led import LED
from button import Button
from utils import format_value, calculate_air_score

class AirQuality:
    """Collects data from sensors and prints to the serial port."""

    def __init__(self, led, button):

        """Initialize the AirQuality class with LED, button, and logger."""
        self.led = led
        self.button = button

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
        self.logging = False
        self.led.blink_once(color='magenta')  # Indicate system is ready

        self._shutdown = False  # Flag to indicate if a safe shutdown has been initiated

    def safe_shutdown(self):
        """Perform safe shutdown actions: log, LED, and optionally power down hardware."""
        msg = "Safe shutdown initiated."
        print(msg)
        self.led.blink_once('yellow')
        self.led.off()
        self._shutdown = True  # Set a flag to indicate shutdown
        time.sleep(1)  # Allow time for LED blink before turning off

    def read_all_sensors(self):
        """Reads all connected air quality sensors, handling I2C and runtime errors gracefully."""
        # Reinitialize values as None each loop to handle sensor read failures gracefully
        co2_value = None
        temp_value = None
        humidity_value = None
        voc_raw = None
        pm = None

        try:
            # SCD4x CO2
            if self.co2_sensor.data_ready:
                co2_value = self.co2_sensor.CO2
        except (OSError, RuntimeError) as e:
            print(f"Error reading CO2 sensor: {e}")
            self.led.blink_once(duration = 1)

        try:
            # SHT4x temp / RH
            temp_value = self.temp_humidity_sensor.temperature
            humidity_value = self.temp_humidity_sensor.relative_humidity
        except (OSError, RuntimeError) as e:
            print(f"Error reading temperature/humidity sensor: {e}")
            self.led.blink_once(duration = 1)

        try:
            # SGP40 raw VOC reading
            voc_raw = self.voc_sensor.measure_raw(temp_value, humidity_value)
        except (OSError, RuntimeError) as e:
            print(f"Error reading VOC sensor: {e}")
            self.led.blink_once(duration = 1)

        try:
            # PM25 dict
            pm = self.pm_sensor.read()
        except (OSError, RuntimeError) as e:
            print(f"Error reading PM sensor: {e}")
            self.led.blink_once(duration = 1)

        return co2_value, temp_value, humidity_value, voc_raw, pm

    async def run(self):
        sensor_interval = 5  # seconds
        last_sensor_time = time.time()
        while True:
            # Check for safe shutdown (button held)
            if self.button.held(hold_time=2.0):
                self.safe_shutdown()

            if self._shutdown:
                break  # Exit the loop if a safe shutdown has been initiated

            # Check button frequently
            if self.button.pressed():
                self.logging = not self.logging
                if self.logging:
                    print("Logging started.")
                else:
                    print("Logging stopped.")
                self.led.blink_once(color='blue')

            now = time.time()
            if (now - last_sensor_time) >= sensor_interval:
                # Read all sensors and handle errors gracefully
                co2_value, temp_value, humidity_value, voc_raw, pm = self.read_all_sensors()

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

                # If logging, print data to console instead of logging to SD card
                if self.logging:
                    print("LOGGING PLACEHOLDER")
                    self.led.blink_once('blue')

                else:
                    air_score = calculate_air_score(co2_value, temp_value, humidity_value, voc_raw, pm)
                    self.led.set_color_by_score(air_score)

                last_sensor_time = now

            await asyncio.sleep(0.01)  # Yield to event loop, check button frequently

if __name__ == "__main__":
    # --- Init objects ---
    led = LED()
    button = Button()

    try:
        air_quality = AirQuality(led, button)

        try:
            asyncio.run(air_quality.run())

        except KeyboardInterrupt:
            print("Program interrupted by user.")
            air_quality.safe_shutdown()

        except Exception as e:
            print(f'Error: {e}')
            air_quality.safe_shutdown()
            led.error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.error_blink()



