class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, pin, brightness=0.2):
        import neopixel
        self.pixels = neopixel.NeoPixel(pin, 1, brightness=brightness, auto_write=False)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def set_color(self, color):
        """Set the LED to a specific color."""
        self.pixels.fill(color)
        self.pixels.show()

    def set_color_by_score(self, air_score):
        """Map air_score to a color and set the LED."""
        if air_score is None:
            color = (0, 0, 255)  # blue = sensor not ready / unknown
        elif air_score <= 15:
            color = self._lerp_color((0, 255, 0), (255, 255, 0), air_score / 5.0)
        elif air_score <= 30:
            color = self._lerp_color((255, 255, 0), (255, 128, 0), (air_score - 5) / 10.0)
        elif air_score <= 50:
            color = self._lerp_color((255, 128, 0), (255, 0, 0), (air_score - 15) / 15.0)
        else:
            color = (255, 0, 0)

        self.set_color(color)

    def _clamp(self, x, lo, hi):
        return lo if x < lo else hi if x > hi else x

    def _lerp_color(self, c1, c2, t):
        """Linear interpolate between two RGB tuples."""
        t = self._clamp(t, 0.0, 1.0)
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )