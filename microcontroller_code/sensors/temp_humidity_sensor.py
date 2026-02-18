

class SHT45:
    """ Class for the SHT45 temperature and humidity sensor. """

    def __init__(self, i2c):
        self.i2c = i2c
        self.address = 0x44

    def read_temperature_humidity(self):
        """ Reads the temperature and humidity from the sensor. """
