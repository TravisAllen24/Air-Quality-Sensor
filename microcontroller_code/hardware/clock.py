from adafruit_pcf8523.pcf8523 import PCF8523 # type: ignore

from utils import format_rtc_dt

class Clock:
    def __init__(self, i2c, internal_rtc):
        self.i2c = i2c
        self.hardware_rtc = PCF8523(self.i2c) # RTC: PCF8523 (RTC)
        # Update internal clock
        self.internal_rtc = internal_rtc
        self.sync()

    def sync(self):
        """Manually realign the internal clock to the accurate hardware clock."""
        self.internal_rtc.datetime = self.hardware_rtc.datetime

    @property
    def battery_low(self) -> bool:
        """Check if the RTC battery is low."""
        return self.hardware_rtc.battery_low

    @property
    def hardware_now(self) -> str:
        return format_rtc_dt(self.hardware_rtc.datetime)

    @property
    def internal_now(self) -> str:
        return format_rtc_dt(self.internal_rtc.datetime)

    @property
    def datetime(self):
        return self.internal_rtc.datetime

    @datetime.setter
    def datetime(self, dt):
        self.hardware_rtc.datetime = dt
        self.sync()
