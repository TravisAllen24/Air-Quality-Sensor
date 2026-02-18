

class SGP40:
    """ Class for the SGP40 VOC sensor. """

    def __init__(self, i2c):
        self.i2c = i2c
        self.address = 0x59

    def read_voc(self):
        """ Reads the VOC value from the sensor. """
