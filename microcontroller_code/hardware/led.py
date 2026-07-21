from time import sleep
import time

from hardware.led_patterns import (ROW_ORDER, COLOR_MAPPING, OFF, 
                                   SNAKE, CONTRACTING_SQUARE, EXPANDING_SQUARE, 
                                   EXCLAMATION, SPIRAL)

from utils import power_guarded, rgb_color_wheel

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self,  matrix, pixel, blue_led, pixel_power, brightness=0.2):
        self._matrix = matrix
        self._pixel = pixel
        self._blue_led = blue_led
        self._brightness = brightness
        self._matrix.brightness = brightness
        self._pixel.brightness = brightness
        self._pixel_power = pixel_power


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
    def show_pattern(self, pattern, color, rgb_color=None):
        # Turns on leds in list and turns off the rest
        if rgb_color is not None:
            led_color = rgb_color
        else:
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

    def animate_with_color_wheel(self, pattern: list[list[int]], delay = 0.05, duration = 5):
        NEXT_COL = 0.01
        next_color_step = 0.01
        color_index = 0
        r,g,b = rgb_color_wheel(color_index)

        start_time = time.monotonic()
        while time.monotonic() - start_time < duration:
            for frame in pattern:
                if time.monotonic() > NEXT_COL + next_color_step:
                    color_index += 1
                    # Get the R,G,B values of the next color
                    r,g,b = rgb_color_wheel( color_index )

                    NEXT_COL = time.monotonic()
                    
                self.show_pattern(frame, color=None, rgb_color=(r,g,b))
                sleep(delay)

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

    @power_guarded()
    def log_data_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(SNAKE, color, delay)

    @power_guarded()
    def spiral(self, duration = 5, delay = 0.05):
        self.animate_with_color_wheel(SPIRAL, delay=delay, duration=duration)
