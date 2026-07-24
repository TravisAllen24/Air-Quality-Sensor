from digitalio import DigitalInOut, Direction  # type: ignore
from analogio import AnalogIn  # type: ignore
from os import statvfs  # type: ignore
import digitalio  # type: ignore
import neopixel  # type: ignore
import board  # type: ignore
import busio  # type: ignore
import rtc  # type: ignore
import gc  # type: ignore

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
        self._pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.3, 
                                        auto_write=False)

        # Create a NeoPixel matrix reference
        self._matrix = neopixel.NeoPixel(board.NEOPIXEL_MATRIX, 49, brightness=0.3, 
                                         auto_write=False)

        # setup i2c
        self._i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)

        # setup RTC
        self._internal_rtc = rtc.RTC()

        # Setup button
        self._btn = digitalio.DigitalInOut(board.IO0)
        self._btn.direction = digitalio.Direction.INPUT
        self._btn.pull = digitalio.Pull.UP

        # setup SPI
        self._spi = board.SPI()
        self._cs_pin = board.D10


    def set_pixel_power(self, state):
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

    def get_sd_card_info(self):
        flash = statvfs('/sd')
        flash_size = flash[0] * flash[2]
        flash_free = flash[0] * flash[3]
        return flash_size, flash_free


    @property
    def i2c(self):
        return self._i2c

    @property
    def spi(self):
        return self._spi, self._cs_pin

    @property
    def cs_pin(self):
        return self._cs_pin

    @property
    def internal_rtc(self):
        return self._internal_rtc

    @property
    def button_pin(self):
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
    def pixel_power(self):
        return self._pixel_power
    
    @property
    def flash_info(self):
        return self.get_flash_info()

    @property
    def blue_led(self):
        return self._led13

    @blue_led.setter
    def blue_led(self,value):
        # Turn the Blue LED on or off
        self._led13.value = value

    def startup_message(self, clock_battery_low=None):
        # Turn on the power to the NeoPixel matrix
        self.set_pixel_power(True)

        # Say hello
        print("\nHello from FeatherS3 Neo!")
        print("-------------------------\n")

        # Show available memory
        print("Memory Info - gc.mem_free()")
        print("---------------------------")
        print(f"{gc.mem_free()/1024/1024} Megabytes\n")  # type: ignore

        # Show flash size
        # CircuitPython reserves a bunch of flash space for other features like OTA updates.
        # If you would like to have access more of the 4MB of flash, you will need to compile
        # your own CircuitPython firmware with a custom flash partition layout
        flash_size, flash_free = self.flash_info
        print("Flash - os.statvfs('/')")
        print("---------------------------")
        print(f"Partition Size: {flash_size/1024/1024} Megabytes\nFree: {flash_free/1024/1024} Megabytes\n")

        # Show sd size
        sd_size, sd_free = self.get_sd_card_info()
        print("SD Card - os.statvfs('/sd')")
        print("---------------------------")
        print(f"Partition Size: {sd_size/1024/1024} Megabytes\nFree: {sd_free/1024/1024} Megabytes\n")

        # Get VBAT voltage
        print("Approximate VBAT voltage")
        print("------------------------")
        print(f"{self.battery_voltage}v\n")

        # Check 5V Sense
        print("Is 5V (VBUS) present?")
        print("---------------------")
        print(f"{self.vbus_present}\n")

        # Show clock battery status
        if clock_battery_low == True:
            print("Is RTC battery low?")
            print("------------------")
            print(f"{clock_battery_low}\n")
