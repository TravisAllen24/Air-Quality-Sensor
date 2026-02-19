"""Main CircuitPython code that collects data from the I2C sensors and prints to serial."""

import time
import board
import busio
import neopixel

import adafruit_scd4x
import adafruit_sht4x
import adafruit_sgp40
from adafruit_pm25.i2c import PM25_I2C

from led import LED



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

        # -------------------------
        # CO2 / T / RH: SCD4x
        # -------------------------
        self.co2_sensor = adafruit_scd4x.SCD4X(self.i2c)
        self.co2_sensor.start_periodic_measurement()

        # -------------------------
        # Temp / RH: SHT4x
        # -------------------------
        self.temp_humidity_sensor = adafruit_sht4x.SHT4x(self.i2c)

        # -------------------------
        # VOC: SGP40
        # -------------------------
        self.voc_sensor = adafruit_sgp40.SGP40(self.i2c)

        # -------------------------
        # PM: PMSA003I via adafruit_pm25 (I2C)
        # -------------------------
        self.pm_sensor = PM25_I2C(self.i2c, reset_pin=None)

        # Warmup tracking (SGP40 & SCD4x like a little time)
        self.start_time = time.monotonic()

    def calculate_air_score(self, co2, temp_c, rh, voc_raw, pm25):
        """
        Air Comfort/Health Score: 0 (excellent) → 100 (very poor)

        Components:
          - CO2 (ventilation / drowsiness)         : 0–30
          - PM2.5 (health)                         : 0–30
          - VOC (irritants/odors proxy, raw scaled): 0–15
          - Temperature comfort (around ~22–24 C)   : 0–15
          - Humidity comfort (30–60% ideal)        : 0–10

        Notes:
          - VOC is still a heuristic unless you compute a VOC index.
          - Temp/RH are comfort-focused, not medical.
        """

        # Reasonable defaults if a sensor isn't ready
        if co2 is None:
            co2 = 400
        if pm25 is None:
            pm25 = 0
        if voc_raw is None:
            voc_raw = 0
        if temp_c is None:
            temp_c = 23.0
        if rh is None:
            rh = 45.0

        # --------------------
        # CO2 score (0–30)
        # --------------------
        # 400–800 good, 800–1200 mild, 1200–2000 worse, >2000 poor
        if co2 <= 800:
            co2_score = 0.0
        elif co2 <= 1200:
            co2_score = (co2 - 800) / 400 * 10.0
        elif co2 <= 2000:
            co2_score = 10.0 + (co2 - 1200) / 800 * 20.0
        else:
            co2_score = 30.0

        # --------------------
        # PM2.5 score (0–30)
        # --------------------
        # Rough health bands: <=5 great, 5–12 ok, 12–35 moderate, >35 poor
        if pm25 <= 5:
            pm_score = 0.0
        elif pm25 <= 12:
            pm_score = (pm25 - 5) / 7 * 8.0
        elif pm25 <= 35:
            pm_score = 8.0 + (pm25 - 12) / 23 * 17.0
        else:
            pm_score = 30.0

        # --------------------
        # VOC raw score (0–15)
        # --------------------
        # Empirical: treat 10k as "clean baseline", 50k as "high"
        voc_norm = min(max((voc_raw - 10000) / 40000, 0.0), 1.0)
        voc_score = voc_norm * 15.0

        # --------------------
        # Temperature comfort (0–15)
        # --------------------
        # Ideal band: 21–24 C (very comfortable for many indoors)
        # Mild discomfort: 18–21 and 24–27
        # Strong discomfort outside that
        if 21.0 <= temp_c <= 24.0:
            temp_score = 0.0
        elif 18.0 <= temp_c < 21.0:
            temp_score = (21.0 - temp_c) / 3.0 * 7.0
        elif 24.0 < temp_c <= 27.0:
            temp_score = (temp_c - 24.0) / 3.0 * 7.0
        else:
            # Outside 18–27 ramps up quickly to max
            # 15C or 30C and beyond => max penalty
            dist = min(max(abs(temp_c - 22.5) - 4.5, 0.0), 7.5)  # 0..7.5
            temp_score = min(7.0 + (dist / 7.5) * 8.0, 15.0)

        # --------------------
        # Humidity comfort (0–10)
        # --------------------
        # Ideal: 30–60%
        # Mild: 20–30 or 60–70
        # Strong: <20 or >70
        if 30.0 <= rh <= 60.0:
            rh_score = 0.0
        elif 20.0 <= rh < 30.0:
            rh_score = (30.0 - rh) / 10.0 * 4.0
        elif 60.0 < rh <= 70.0:
            rh_score = (rh - 60.0) / 10.0 * 4.0
        else:
            # Outside 20–70 ramps to max
            if rh < 20.0:
                rh_score = min(4.0 + (20.0 - rh) / 20.0 * 6.0, 10.0)  # 0% -> 10
            else:  # rh > 70
                rh_score = min(4.0 + (rh - 70.0) / 30.0 * 6.0, 10.0)  # 100% -> 10

        air_score = co2_score + pm_score + voc_score + temp_score + rh_score
        air_score = min(max(air_score, 0.0), 100.0)
        return round(air_score, 2)


    def run(self):
        while True:
            # -------------------------
            # SCD4x CO2
            # -------------------------
            co2_value = None
            scd_temp = None
            scd_rh = None
            if self.co2_sensor.data_ready:
                co2_value = self.co2_sensor.CO2
                scd_temp = self.co2_sensor.temperature
                scd_rh = self.co2_sensor.relative_humidity

            # -------------------------
            # SHT4x temp / RH
            # -------------------------
            temp_value = self.temp_humidity_sensor.temperature
            humidity_value = self.temp_humidity_sensor.relative_humidity

            # -------------------------
            # SGP40 raw VOC reading
            # -------------------------
            voc_raw = None
            voc_raw = self.voc_sensor.measure_raw(temp_value, humidity_value)

            # -------------------------
            # PM25 dict
            # -------------------------
            pm = None
            pm25_std = None

            pm = self.pm_sensor.read()
            # Common keys: "pm10 standard", "pm25 standard", "pm100 standard"
            pm25_std = pm.get("pm25 standard", None)


            air_score = self.calculate_air_score(co2_value, temp_value, humidity_value, voc_raw, pm25_std)

            # Print a nice line
            print(
                "CO2: {} ppm | SHT T: {:.2f} C RH: {:.2f}% | VOC: {} | PM: {} | Score: {:.3f}".format(
                    co2_value if co2_value is not None else "----",
                    temp_value,
                    humidity_value,
                    voc_raw,
                    pm,
                    air_score,
                )
            )

            self.led.set_color_by_score(air_score)
            time.sleep(5)


if __name__ == "__main__":
    AirQuality().run()

