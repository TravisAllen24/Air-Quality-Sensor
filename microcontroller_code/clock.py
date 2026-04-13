from adafruit_pcf8523.pcf8523 import PCF8523 # type: ignore

from utils import format_rtc_dt

class RTC:

    def __init__(self, i2c):
        self.i2c = i2c
        self.rtc = PCF8523(self.i2c) # RTC: PCF8523 (RTC)

    @property
    def now(self) -> str:
        return format_rtc_dt(self.rtc.datetime)