import busio # type: ignore
import board # type: ignore

class I2C(busio.I2C):
    """Initialize I2C bus."""
    # Initialize I2C (and wait until ready)
    def __init__(self):
        super().__init__(board.SCL, board.SDA, frequency=100_000)
        while not self.try_lock():
            pass
        self.unlock()
