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