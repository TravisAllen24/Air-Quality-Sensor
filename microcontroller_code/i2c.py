import busio # type: ignore
import board # type: ignore

class I2C:
    def __init__(self):
        """Initialize I2C bus."""
        # Initialize I2C (and wait until ready)
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)
        while not i2c.try_lock():
            pass
        i2c.unlock()