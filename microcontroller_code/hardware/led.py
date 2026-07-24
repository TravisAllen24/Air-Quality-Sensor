from time import sleep
import time

from hardware.led_patterns import (ROW_ORDER, COLOR_MAPPING, OFF, 
                                   SNAKE, CONTRACTING_SQUARE, EXPANDING_SQUARE, 
                                   EXCLAMATION, SPIRAL)

from utils import power_guarded, rgb_color_wheel

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self,  matrix, pixel, blue_led, pixel_power, cfg):
        self._matrix = matrix
        self._pixel = pixel
        self._blue_led = blue_led
        brightness = cfg.get("led.matrix_brightness", 0.2)
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

    def blink(self, color, duration=0.25, blinks=1):      
        for _ in range(blinks):
            self.on(color)
            sleep(duration)
            self.off()
            sleep(duration)

    def blue_on(self):
        self._blue_led.value = True

    def blue_off(self):
        self._blue_led.value = False

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
        self._matrix.show()
        self._pixel.show()

    def all_off(self):
        self._matrix.fill(OFF)
        self._pixel.fill(OFF)
        self._matrix.show()
        self._pixel.show()

    def all_blink_once(self, color = 'red', duration = 0.25):
        self.all_on(color)
        sleep(duration)
        self.all_off()


    # List methods
    def show_pattern(self, pattern, color: str|None="blue", rgb_color:tuple|None=None):
        # Turns on leds in list and turns off the rest
        if rgb_color and not color:
            led_color = rgb_color
        elif color:
            led_color = COLOR_MAPPING.get(color, OFF)
        else:
            led_color = OFF

        for i in range(len(self._matrix)):
            if i in pattern:
                self._matrix[i] = led_color
            else:
                self._matrix[i] = OFF

        self._pixel.fill(led_color)
        self._matrix.show()
        self._pixel.show()  

    def blink_pattern(self, pattern: list[int], color, duration = 0.25, blinks = 1):
        for _ in range(blinks):
            self.show_pattern(pattern, color)
            sleep(duration)
            self.all_off()
            sleep(duration)

    def animate_pattern(self, pattern: list[list[int]], color, delay = 0.05):
        for frame in pattern:
            self.show_pattern(frame, color)
            sleep(delay)
            
        self.all_off()

    def animate_with_color_wheel(self, pattern, delay=0.05, duration=5, color_step=1, color_index=0):
        color_pos = color_index
        r, g, b = rgb_color_wheel(color_pos)

        start_time = time.monotonic()
        while time.monotonic() - start_time < duration:
            for frame in pattern:
                color_pos += color_step
                r, g, b = rgb_color_wheel(color_pos)
                self.show_pattern(frame, color=None, rgb_color=(r, g, b))
                sleep(delay)
        self.all_off()


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
    def error_blink(self, color = 'red', duration = 0.25, blinks = 3):
        self.blink_pattern(EXCLAMATION, color, duration, blinks=blinks)

    @power_guarded(fallback_blinks=3, fallback_duration=0.1)
    def warning_blink(self, color = 'orange', duration = 0.25, blinks = 3):
        self.blink_pattern(EXCLAMATION, color, duration, blinks=blinks)

    @power_guarded(fallback_blinks=1000, fallback_duration=1)
    def continuous_error_blink(self, color = 'red', duration = 0.25):
        while True:
            self.blink_pattern(EXCLAMATION, color, duration)
            sleep(duration)

    @power_guarded(fallback_blinks=3, fallback_duration=1)
    def startup_blink(self, color = 'white', delay = 0.1):
        self.animate_pattern(EXPANDING_SQUARE, color, delay)

    @power_guarded(fallback_blinks=2, fallback_duration=1)
    def shutdown_blink(self, color = 'orange', delay = 0.1):
        self.animate_pattern(CONTRACTING_SQUARE, color, delay)

    @power_guarded(fallback_blinks=3)
    def start_log_blink(self, color='blue', delay=0.1):
        self.animate_pattern(EXPANDING_SQUARE, color, delay)

    @power_guarded(fallback_blinks=2)
    def stop_log_blink(self, color = 'blue', delay = 0.1):
        self.animate_pattern(CONTRACTING_SQUARE, color, delay)

    @power_guarded()
    def log_data_blink(self, color = 'blue', delay = 0.025):
        self.animate_pattern(SNAKE, color, delay)

    @power_guarded()
    def spiral(self, duration = 5, delay = 0.05):
        self.animate_with_color_wheel(SPIRAL, delay=delay, duration=duration)
