import time

class Button:
    def __init__(self, btn_pin):
        self._btn = btn_pin
        self._press_start = None
        self._released = True
        self._released_hold_time = 0.0  # set once on release; consumed by caller

    def update(self):
        """Call frequently to update button state."""
        current = self._btn.value  # active low: False == pressed

        if not current and self._released:
            self._press_start = time.monotonic()
            self._released = False
        elif current and not self._released:
            if self._press_start is not None:
                self._released_hold_time = time.monotonic() - self._press_start
            self._press_start = None
            self._released = True

    def consume_released_hold_duration(self):
        """Return and clear the duration of the most recently completed press. Call once per use."""
        t = self._released_hold_time
        self._released_hold_time = 0.0
        return t
    
    def current_hold_duration(self):
        """Live duration the button has been held so far; 0.0 if not currently pressed."""
        if self._press_start is None:
            return 0.0
        return time.monotonic() - self._press_start
    
    def shutdown_press(self, threshold=2.0):
        """Return True if the button is currently being held for a shutdown."""
        return self.current_hold_duration() >= threshold
    
    def logging_press(self, threshold=2.0):
        held = self.consume_released_hold_duration()
        if 0.0 < held < threshold:
            return True
        return False
