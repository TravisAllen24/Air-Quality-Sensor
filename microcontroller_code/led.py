import asyncio
from time import sleep

import neopixel # type: ignore
import board # type: ignore

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

# Define patterns
SKULL = [1,2,3,4,5,7,8,9,10,11,12,13,14,17,20,21,24,27,29,30,32,33,37,38,39,44,45,46]
X_BLINK = [0,1,5,6,7,8,9,11,12,13,15,16,17,18,19,23,24,25,29,30,31,32,33,35,36,37,39,40,41,42,43,47,48]
ER = [7,8,9,14,18,20,21,22,23,25,26,28,32,35,36,37,39]
SNAKE = [0,1,2,3,4,5,6,12,18,24,30,36,42,48,47,46,45,44,43,37,31,25,19,13,7]
WIND = [1,2,7,8,9,10,13,14,17,18,19,20,22,23,25,26,28,29,30,31,34,35,38,39,40,41,46,47]
TORNADO_1 = [0,1,2,3,4,5,6,8,9,15,16,17,18,19,24,25,30,31,32,38,45]
TORNADO_2 = [0,1,2,3,4,5,6,10,11,12,13,15,16,22,23,24,25,26,31,32,37,38,39,45]
EXCLAMATION = [10,17,24,38]


SKULL =    [[0,1,1,1,1,1,0],
            [1,1,1,1,1,1,1],
            [1,0,0,1,0,0,1],
            [1,0,0,1,0,0,1],
            [0,1,1,0,1,1,0],
            [0,0,1,1,1,0,0],
            [0,0,1,1,1,0,0]]

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, pin = board.NEOPIXEL, brightness=0.2):
        self.pixels = neopixel.NeoPixel(pin, 49, brightness=brightness)
        self.pixels.fill(OFF)


    # Individial pixel methods
    def on(self, n, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self.pixels[n] = led_color


    def off(self, n):
        self.pixels[n] = OFF


    # All pixels methods
    def all_on(self, color):
        led_color = COLOR_MAPPING.get(color, OFF)
        self.pixels.fill(led_color)
    

    def all_off(self):
        self.pixels.fill(OFF)


    def blink_once(self, color = 'red', duration = 0.25):
        self.all_on(color)
        sleep(duration)
        self.all_off()


    # List methods
    def set_pixel_list(self, pattern, color):
        # Turns on leds in list and turns off the rest
        led_color = COLOR_MAPPING.get(color, OFF)
        for i in range(len(self.pixels)):
            if i in pattern:
                self.pixels[i] = led_color
            else:
                self.pixels[i] = OFF
        

    def blink_pixel_list(self, pattern, color, duration = 0.25):
        self.set_pixel_list(pattern, color)
        sleep(duration)
        self.all_off()


    def show_air_score(self, colors_mags_dict):
        self.all_off()

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


    def snake(self, color = 'green', delay = 0.02, loops = 1):
        self.all_off()
        snake_len = 5
        for _ in range(loops):
            for i in range(len(SNAKE)):
                snake_body = []
                for j in reversed(range(snake_len)):
                    snake_body.append(SNAKE[(i-j + snake_len - 1) % len(SNAKE)])
                
                self.set_pixel_list(snake_body, color)
                sleep(delay)

    def expanding_ring(self, color = 'white', delay = 0.05):
        pass


    def contracting_ring(self, color = 'yellow', delay = 0.05):
        pass


    # Information and logging methods
    def error_blink(self, color = 'red', duration = 0.25):
        self.blink_pixel_list(EXCLAMATION, color, duration)

    def warning_blink(self, color = 'yellow', duration = 0.25):
        self.blink_pixel_list(EXCLAMATION, color, duration)

    def continuous_error_blink(self, color = 'red', on_duration = 0.25, off_duration = 1):
        while True:
            self.blink_pixel_list(EXCLAMATION, color, on_duration)
            sleep(off_duration)

    def continuous_warning_blink(self, color = 'yellow', on_duration = 0.25, off_duration = 1):
        while True:
            self.blink_pixel_list(EXCLAMATION, color, on_duration)
            sleep(off_duration)

    def startup_blink(self, color = 'white', delay = 0.05):
        self.expanding_ring(color, delay)

    def start_log_blink(self, color = 'blue', delay = 0.05):
        self.expanding_ring(color, delay)

    def stop_log_blink(self, color = 'blue', delay = 0.05):
        self.contracting_ring(color, delay)

    def log_data_blink(self, color = 'blue', delay = 0.05):
        self.snake(color, delay)
