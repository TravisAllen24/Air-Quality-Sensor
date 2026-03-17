import time
import board # type: ignore
import busio # type: ignore

from adafruit_pcf8523.pcf8523 import PCF8523 # type: ignore

i2c = busio.I2C(board.SCL, board.SDA)
rtc = PCF8523(i2c)

# Set to current time (replace with your actual current time)
# Format: (year, month, day, hour, minute, second, weekday, yearday, isdst)
# Weekday: Monday is 0, Sunday is 6
rtc.datetime = time.struct_time((2026, 3, 2, 14, 58, 0, 0, -1, -1))

