import neopixel
import board
from os import statvfs
from digitalio import DigitalInOut, Direction
from analogio import AnalogIn
import digitalio
import busio
import rtc

class FeatherS3Neo:
    def __init__(self):
        # pin 13 and on-board RGB
        self._led13 = DigitalInOut(board.LED)
        self._led13.direction = Direction.OUTPUT
        
        # Setup the NeoPixel power pins
        self._pixel_power = DigitalInOut(board.NEOPIXEL_POWER)
        self._pixel_power.direction = Direction.OUTPUT
        self._pixel_power.value = True

        # Setup the BATTERY voltage sense pin
        self._vbat_voltage = AnalogIn(board.BATTERY)

        # Setup the VBUS sense pin
        self._vbus_sense = DigitalInOut(board.VBUS_SENSE)
        self._vbus_sense.direction = Direction.INPUT
        
        # Create a NeoPixel reference
        self._pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.3, auto_write=True, pixel_order=neopixel.RGB)

        # Create a NeoPixel matrix reference
        self._matrix = neopixel.NeoPixel(board.NEOPIXEL_MATRIX, 49, brightness=0.3, auto_write=True, pixel_order=neopixel.RGB)
        
        # Initially set the matrix power off
        self._pixel_power.value = False

        # setup i2c
        self._i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)

        # setup RTC
        self._internal_rtc = rtc.RTC()

        # Setup button
        self._btn = digitalio.DigitalInOut(pin=board.BUTTON)
        self._btn.direction = digitalio.Direction.INPUT
        self._btn.pull = digitalio.Pull.UP
        

    def set_pixel_matrix_power(self, state):
        """Enable or Disable power to the onboard NeoPixel to either show colour, or to reduce power fro deep sleep"""
        self._pixel_power.value = state
    
    def get_battery_voltage(self):
        """Get the approximate battery voltage"""
        # I don't really understand what CP is doing under the hood here for the ADC range & calibration,
        # but the onboard voltage divider for VBAT sense is setup to deliver 1.1V to the ADC based on it's
        # default factory configuration.
        # This forumla should show the nominal 4.2V max capacity (approximately) when 5V is present and the
        # VBAT is in charge state for a 1S LiPo battery with a max capacity of 4.2V   
        return round(self._vbat_voltage.value / 5370,2)

    def get_vbus_present(self):
        """Detect if VBUS (5V) power source is present"""
        return self._vbus_sense.value
    
    def get_flash_info(self):
        flash = statvfs('/')
        flash_size = flash[0] * flash[2]
        flash_free = flash[0] * flash[3]
        return flash_size, flash_free
        

    @property
    def i2c(self):
        """Exposes the shared I2C bus object for down-stream sensors."""
        return self._i2c

    @property
    def internal_rtc(self):
        """Exposes CircuitPython's core software clock instance."""
        return self._internal_rtc

    @property
    def button_pin(self):
        """Exposes the raw hardware button object for your ButtonManager."""
        return self._btn

    @property
    def battery_voltage(self):
        return self.get_battery_voltage()
    
    @property
    def vbus_present(self):
        return self.get_vbus_present()
    
    @property
    def pixel(self):
        return self._pixel
    
    @property
    def matrix(self):
        return self._matrix
    
    @property
    def flash_info(self):
        return self.get_flash_info()
    
    @property
    def blue_led(self):
        return self._led13.value
    
    @blue_led.setter
    def blue_led(self,value):
        # Turn the Blue LED on or off
        self._led13.value = value
        