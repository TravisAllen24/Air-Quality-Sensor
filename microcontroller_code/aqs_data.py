from dataclasses import dataclass
from utils import c_to_f

@dataclass
class AQSData:
    """Data structure to hold air quality sensor readings."""
    datetime: str|None
    temp: float|None
    humidity: float|None
    dp: float|None
    co2: int|None
    voc_raw: int|None
    voc_index: int|None
    nox_raw: int|None
    nox_index: int|None
    pm10: float|None
    pm25: float|None
    pm100: float|None

    def convert_to_fahrenheit(self):
        self.temp = c_to_f(self.temp)
        self.dp = c_to_f(self.dp)
        return self
