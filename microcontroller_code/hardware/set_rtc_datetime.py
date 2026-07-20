import time
from i2c import I2C
from clock import Clock
import rtc
# Set to current time (replace with your actual current time)

year = 2026
month = 5
day = 27
hour = 19
minute = 38
second = 0

# Format: (year, month, day, hour, minute, second, weekday, yearday, isdst)
# Weekday: Monday is 0, Sunday is 6
i2c = I2C()
internal_rtc = rtc.RTC()  # Replace with your actual internal RTC object if needed
clock = Clock(i2c, internal_rtc)  # Replace None with your actual I2C object if needed
clock.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))

print(f"Adalogger RTC datetime set to: {clock.hardware_now}")
print(f"Internal RTC datetime set to: {clock.internal_now} (should equal the Adalogger RTC datetime)")

