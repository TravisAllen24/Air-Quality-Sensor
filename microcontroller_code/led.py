import neopixel

class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, pin, brightness=0.2):
        self.pixels = neopixel.NeoPixel(pin, 1, brightness=brightness, auto_write=False)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def set_color(self, color):
        """Set the LED to a specific color."""
        self.pixels.fill(color)
        self.pixels.show()

    def set_color_by_score(self, air_score):
        """Map air_score to a color and set the LED.
        
        Args:
            air_score (int): Air quality score between 0 (good) and 100 (bad).
        """
        # Ensure air_score is within bounds
        air_score = max(0, min(100, air_score))

        # Calculate the red and green components for the gradient
        red = int((air_score / 100) * 255)
        green = int((1 - air_score / 100) * 255)

        # Set the LED color
        self.set_color((red, green, 0))
