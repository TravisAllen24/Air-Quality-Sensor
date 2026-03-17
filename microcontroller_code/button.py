import digitalio # type: ignore
import board # type: ignore
import time

class Button:
    def __init__(self, pin=board.BUTTON, pull=digitalio.Pull.UP):
        self._btn = digitalio.DigitalInOut(pin)
        self._btn.direction = digitalio.Direction.INPUT
        self._btn.pull = pull
        self._last = self._btn.value
        self._press_start = None
        self._hold_time = 0.0
        self._released = True

    def update(self):
        """Call this method frequently to update button state."""
        current = self._btn.value
        # Button pressed (active low)
        if not current and self._released:
            self._press_start = time.monotonic()
            self._released = False
        elif current and not self._released:
            # Button released
            if self._press_start is not None:
                self._hold_time = time.monotonic() - self._press_start
            else:
                self._hold_time = 0.0
            self._press_start = None
            self._released = True
        self._last = current

    def held(self):
        """Return the time the button was held (in seconds) since last release, and reset hold time."""
        if self._hold_time > 0.0:
            t = self._hold_time
            self._hold_time = 0.0
            return t
        return 0.0
