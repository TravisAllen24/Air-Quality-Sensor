from time import sleep

import neopixel # type: ignore
import board # type: ignore

from led_patterns import SNAKE, EXPANDING_SQUARE, EXCLAMATION, TORNADO_1, TORNADO_2, HEART

# Define a color mapping for common color names
OFF = (0, 0, 0)

COLOR_MAPPING = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "orange": (255, 165, 0),
    "off": OFF,
}

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, pin = board.NEOPIXEL_MATRIX, brightness=0.2):
        self.pixels = neopixel.NeoPixel(pin, 49, brightness=brightness, auto_write=False)
        self.pixels.fill(OFF)
        self.pixels.show()


    # Individial pixel methods
    def on(self, n, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self.pixels[n] = led_color
        self.pixels.show()


    def off(self, n):
        self.pixels[n] = OFF
        self.pixels.show()


    # All pixels methods
    def all_on(self, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self.pixels.fill(led_color)
        self.pixels.show()


    def all_off(self):
        self.pixels.fill(OFF)
        self.pixels.show()


    def blink_once(self, color = 'red', duration = 0.25):
        self.all_on(color)
        sleep(duration)
        self.all_off()


    # List methods
    def show_pattern(self, pattern, color):
        # Turns on leds in list and turns off the rest
        led_color = COLOR_MAPPING.get(color, OFF)
        for i in range(len(self.pixels)):
            if i in pattern:
                self.pixels[i] = led_color
            else:
                self.pixels[i] = OFF
        self.pixels.show()

    def blink_pattern(self, pattern: list[int], color, duration = 0.25):
        self.show_pattern(pattern, color)
        sleep(duration)
        self.all_off()

    def animate_pattern(self, pattern: list[list[int]], color, delay = 0.05):
        for frame in pattern:
            self.show_pattern(frame, color)
            sleep(delay)

    def show_air_score(self, colors_mags_dict):
        self.pixels.fill(OFF)

        column_pixels = {   "temp": [0, 7, 14, 21, 28, 35, 42],
                            "rh": [1, 8, 15, 22, 29, 36, 43],
                            "co2": [2, 9, 16, 23, 30, 37, 44],
                            "voc": [3, 10, 17, 24, 31, 38, 45],
                            "nox": [4, 11, 18, 25, 32, 39, 46],
                            "pm": [5, 12, 19, 26, 33, 40, 47],
                            "air": [6, 13, 20, 27, 34, 41, 48]}

        for column, pixels_list in column_pixels.items():
            color = colors_mags_dict[column]["color"]
            pixels = pixels_list[:colors_mags_dict[column]["mag"]]
            for pixel in pixels:
                self.pixels[pixel] = color

        self.pixels.show()

    # Wrappers
    def error_blink(self, color = 'red', duration = 0.25):
        self.blink_pattern(EXCLAMATION, color, duration)

    def warning_blink(self, color = 'yellow', duration = 0.25):
        self.blink_pattern(EXCLAMATION, color, duration)

    def continuous_error_blink(self, color = 'red', duration = 0.25):
        while True:
            self.blink_pattern(EXCLAMATION, color, duration)
            sleep(1)

    def startup_blink(self, color = 'white', delay = 0.1):
        self.animate_pattern(EXPANDING_SQUARE, color, delay)

    def shutdown_blink(self, color = 'yellow', delay = 0.1):
        self.animate_pattern(list(reversed(EXPANDING_SQUARE)), color, delay)

    def start_log_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(EXPANDING_SQUARE, color, delay)

    def stop_log_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(list(reversed(EXPANDING_SQUARE)), color, delay)

    def log_data_blink(self, color = 'blue', delay = 0.05):
        self.animate_pattern(SNAKE, color, delay)

    def tornado(self, color="white", delay=.5):
        self.show_pattern(TORNADO_1, color)
        sleep(delay)
        self.show_pattern(TORNADO_2, color)
        sleep(delay)

    def heart(self, color="red"):
        self.show_pattern(HEART, color)


