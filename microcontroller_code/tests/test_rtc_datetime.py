"""Test script to read and print the current datetime from the PCF8523 RTC."""

import board # type: ignore
import busio # type: ignore
from adafruit_pcf8523.pcf8523 import PCF8523 # type: ignore

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
rtc = PCF8523(i2c)

# Read datetime from RTC
current_time = rtc.datetime

# Print the datetime in a readable format
print("RTC datetime:", current_time)
print("Formatted: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
    current_time.tm_year, current_time.tm_mon, current_time.tm_mday,
    current_time.tm_hour, current_time.tm_min, current_time.tm_sec
))
