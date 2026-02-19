class LED:
    """Handles LED operations, including color mapping and updates."""

    def __init__(self, neopixel, pin, brightness=0.2):
        self.pixels = neopixel.NeoPixel(pin, 1, brightness=brightness, auto_write=False)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def set_color(self, color):
        """Set the LED to a specific coloimport neopixel

class LED:
    """NeoPixel status LED with 0–100 air score mapping (0=best, 100=worst)."""

    def __init__(self, pin, n=1, brightness=0.2):
        self._n = n
        self.pixels = neopixel.NeoPixel(pin, n, brightness=brightness, auto_write=False)
        self.off()

    def off(self):
        self.set_color((0, 0, 0))

    def set_color(self, color):
        """Set all pixels to a specific RGB color tuple."""
        self.pixels.fill(color)
        self.pixels.show()

    @staticmethod
    def _clamp(x, lo, hi):
        return lo if x < lo else hi if x > hi else x

    @staticmethod
    def _lerp_color(c1, c2, t):
        """Linear interpolate between two RGB tuples."""
        t = LED._clamp(t, 0.0, 1.0)
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def set_color_by_score(self, air_score):
        """
        Map 0–100 air_score to a smooth gradient:
          None        -> blue (unknown / not ready)
          0–10        -> green
          10–25       -> green -> yellow
          25–50       -> yellow -> orange
          50–75       -> orange -> red
          75–100+     -> red
        """
        if air_score is None:
            self.set_color((0, 0, 255))  # blue
            return

        s = float(self._clamp(air_score, 0.0, 100.0))

        if s <= 10.0:
            color = (0, 255, 0)  # green
        elif s <= 15:
            # green -> yellow
            color = self._lerp_color((0, 255, 0), (255, 255, 0), (s - 10.0) / 15.0)
        elif s <= 30:
            # yellow -> orange
            color = self._lerp_color((255, 255, 0), (255, 140, 0), (s - 25.0) / 25.0)
        elif s <= 50:
            # orange -> red
            color = self._lerp_color((255, 140, 0), (255, 0, 0), (s - 50.0) / 25.0)
        else:
            color = (255, 0, 0)  # red

        self.set_color(color)

r."""
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