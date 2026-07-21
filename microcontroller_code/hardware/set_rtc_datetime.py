import time

from hardware.feathers3neo import FeatherS3Neo
from hardware.clock import Clock

# Set to current time (replace with your actual current time)
year = 2026
month = 5
day = 27
hour = 19
minute = 38
second = 0

# Format: (year, month, day, hour, minute, second, weekday, yearday, isdst)
# Weekday: Monday is 0, Sunday is 6
feather = FeatherS3Neo()
i2c = feather.i2c
internal_rtc = feather.internal_rtc  # Replace with your actual internal RTC object if needed
clock = Clock(i2c, internal_rtc)  # Replace None with your actual I2C object if needed
clock.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))

print(f"Adalogger RTC datetime set to: {clock.hardware_now}")
print(f"Internal RTC datetime set to: {clock.internal_now} (should equal the Adalogger RTC datetime)")

