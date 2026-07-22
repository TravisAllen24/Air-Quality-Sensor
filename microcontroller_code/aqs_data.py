from dataclasses import dataclass
from utils import c_to_f, format_value

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

    def __str__(self) -> str:
        return f"$AQS,{self.datetime},{self.temp},{self.humidity}, \
                {self.dp},{self.co2},{self.voc_raw},{self.voc_index}, \
                {self.nox_raw},{self.nox_index},{self.pm100}, \
                {self.pm25},{self.pm10}"
    
    def format_to_print(self, temp_unit="C") -> str:
        return ("RTC {} | T: {} {} RH: {}% -> DP: {} {} | CO2: {} ppm |"
                " VOC Raw: {} VOC Index: {} | NOx Raw: {} NOx Index: {} |"
                " PM10: {} PM2.5: {} PM1.0: {}".format(
                        self.datetime,
                        format_value(self.temp, 2), temp_unit,
                        format_value(self.humidity, 2),
                        format_value(self.dp, 2), temp_unit,
                        format_value(self.co2),
                        format_value(self.voc_raw),
                        format_value(self.voc_index),
                        format_value(self.nox_raw),
                        format_value(self.nox_index),
                        format_value(self.pm100),
                        format_value(self.pm25),
                        format_value(self.pm10),
            ))
        
    def convert_to_fahrenheit(self) -> "AQSData":
        self.temp = c_to_f(self.temp)
        self.dp = c_to_f(self.dp)
        return self
    
    @classmethod
    def from_sensor(cls, sensor) -> "AQSData":
        """Alternative constructor to build AQSData directly from a sensor instance."""
        return cls(
            datetime=sensor.clock.internal_now,
            temp=sensor.temp_value,
            humidity=sensor.humidity_value,
            dp=sensor.dew_point,
            co2=sensor.co2_value,
            voc_raw=sensor.voc_raw,
            voc_index=sensor.voc_index,
            nox_raw=sensor.nox_raw,
            nox_index=sensor.nox_index,
            pm10=sensor.pm10,
            pm25=sensor.pm25,
            pm100=sensor.pm100
        )
