import digitalio
import board

class Button:

    def __init__(self, pin = board.BUTTON, pull=digitalio.Pull.UP):
        self._btn = digitalio.DigitalInOut(pin)
        self._btn.direction = digitalio.Direction.INPUT
        self._btn.pull = pull
        self._last = self._btn.value

    def pressed(self):
        current = self._btn.value
        edge = self._last and not current  # pull-up: True→False
        self._last = current
        return edge

    def held(self, hold_time=2.0):
        """Return True if the button is held for hold_time seconds."""
        import time
        if not self._btn.value:  # Button pressed (active low)
            start = time.monotonic()
            while not self._btn.value:
                if (time.monotonic() - start) >= hold_time:
                    # Wait for release to avoid repeated triggers
                    while not self._btn.value:
                        pass
                    return True
        return False
