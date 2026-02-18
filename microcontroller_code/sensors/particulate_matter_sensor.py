

class PMSA003I:
    """ Class for the PMSA003I particulate matter sensor. """

    def __init__(self, i2c):
        self.i2c = i2c
        self.address = 0x44

    def read_pm(self):
        """ Reads the particulate matter values from the sensor. """