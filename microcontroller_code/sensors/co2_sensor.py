

class SCD40:
    """ Class for the SCD40 CO2 sensor. """

    def __init__(self, i2c):
        self.i2c = i2c
        self.address = 0x62

    def read_co2(self):
        """ Reads the CO2 value from the sensor. """