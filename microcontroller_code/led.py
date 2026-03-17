from time import sleep

import neopixel # type: ignore
import board # type: ignore

# Define a color mapping for common color names
COLOR_MAPPING = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "orange": (255, 165, 0),
    "off": (0, 0, 0),
}

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, pin = board.NEOPIXEL, brightness=0.2):
        self.pixels = neopixel.NeoPixel(pin, 1, brightness=brightness, auto_write=False)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        self._is_on = False

    def set_color(self, color: tuple):
        """Set the LED to a specific color."""
        self.pixels.fill(color)
        self.pixels.show()
        self._is_on = True


    def on(self, color):
        led_color = COLOR_MAPPING.get(color, (0, 0, 0))
        self.pixels.fill(led_color)
        self.pixels.show()
        self._is_on = True

    def off(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        self._is_on = False

    def toggle(self, color):
        if self._is_on:
            self.off()
        else:
            self.on(color)
            self._is_on = True

    def blink_once(self, color = 'red', duration = 0.25):
        self.on(color)

        sleep(duration)

        self.off()

    def error_blink(self, color = 'red', duration = 0.25):
        while True:
            self.blink_once(color, duration)

            sleep(1)
