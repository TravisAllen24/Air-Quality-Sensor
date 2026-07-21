from time import sleep
from digitalio import DigitalInOut, Direction # type: ignore
import neopixel # type: ignore
import board # type: ignore

from hardware.led_patterns import ROW_ORDER, COLOR_MAPPING, OFF, SNAKE, EXPANDING_SQUARE, EXCLAMATION
from aqs_settings import load_settings, get
from utils import power_guarded

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self,  matrix, pixel, blue_led, brightness=0.2):
        self._matrix = matrix
        self._pixel = pixel
        self._blue_led = blue_led
        self._brightness = brightness
        self._matrix.brightness = brightness
        self._pixel.brightness = brightness


    # Individual pixel methods
    def on(self, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self._pixel.fill(led_color)
        self._pixel.show()

    def off(self):
        self._pixel.fill(OFF)
        self._pixel.show()

    def blink_once(self, color, duration=0.25, blinks=1):
        led_color = COLOR_MAPPING.get(color, OFF)
        self._pixel.fill(led_color)
        sleep(duration)
        self._pixel.fill(OFF)

    def blue_on(self):
        self._blue_led.value = True
        self._pixel.show()

    def blue_off(self):
        self._blue_led.value = False
        self._pixel.show()

    def blue_blink(self, duration=0.25, blinks=1):
        for _ in range(blinks):
            self.blue_on()
            sleep(duration)
            self.blue_off()
            sleep(duration)


    # All pixels methods
    def all_on(self, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self._matrix.fill(led_color)
        self._pixel.fill(led_color)


    def all_off(self):
        self._matrix.fill(OFF)
        self._pixel.fill(OFF)


    def all_blink_once(self, color = 'red', duration = 0.25):
        self.all_on(color)
        sleep(duration)
        self.all_off()


    # List methods
    def show_pattern(self, pattern, color):
        # Turns on leds in list and turns off the rest
        led_color = COLOR_MAPPING.get(color, OFF)
        for i in range(len(self._matrix)):
            if i in pattern:
                self._matrix[i] = led_color
            else:
                self._matrix[i] = OFF

        self._matrix.show()


    def blink_pattern(self, pattern: list[int], color, duration = 0.25):
        self.show_pattern(pattern, color)
        sleep(duration)
        self.all_off()

    def animate_pattern(self, pattern: list[list[int]], color, delay = 0.05):
        for frame in pattern:
            self.show_pattern(frame, color)
            sleep(delay)

    def spiral(self, color, delay):
        pass


    # Row methods
    def show_air_quality_data(self, row_data, num_cols=7):
        """Light up one row per variable in ROW_ORDER; `mag` pixels lit, left to right."""
        self._matrix.fill(OFF)
        for row_index, key in enumerate(ROW_ORDER):
            color = row_data[key]["color"]
            mag = row_data[key]["mag"]
            row_start = row_index * num_cols
            for offset in range(mag):
                self._matrix[row_start + offset] = color

        self._matrix.show()


    # Wrappers
    @power_guarded(fallback_blinks=5, fallback_duration=.1)
    def error_blink(self, color = 'red', duration = 0.25):
        self.blink_pattern(EXCLAMATION, color, duration)

    @power_guarded(fallback_blinks=3, fallback_duration=0.1)
    def warning_blink(self, color = 'yellow', duration = 0.25):
        self.blink_pattern(EXCLAMATION, color, duration)

    @power_guarded(fallback_blinks=1000, fallback_duration=1)
    def continuous_error_blink(self, color = 'red', duration = 0.25):
        while True:
            self.blink_pattern(EXCLAMATION, color, duration)
            sleep(1)

    @power_guarded(fallback_blinks=3, fallback_duration=1)
    def startup_blink(self, color = 'white', delay = 0.05):
        self.animate_pattern(EXPANDING_SQUARE, color, delay)

    @power_guarded(fallback_blinks=2, fallback_duration=1)
    def shutdown_blink(self, color = 'yellow', delay = 0.05):
        self.animate_pattern(CONTRACTING_SQUARE, color, delay)

    @power_guarded(fallback_blinks=3)
    def start_log_blink(self, color='blue', delay=0.05):
        self.animate_pattern(SNAKE, color, delay)

    @power_guarded(fallback_blinks=2)
    def stop_log_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(CONTRACTING_SQUARE, color, delay)

    def log_data_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(SNAKE, color, delay)
