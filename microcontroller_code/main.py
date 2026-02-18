""" Main micropython code that collects data from the i2c sensors and sends it to the serial port. """
import time
from machine import I2C, Pin, Serial

from sensors.co2_sensor import SCD40
from sensors.temp_humidity_sensor import SHT45
from sensors.voc_sensor import SGP40
from sensors.particulate_matter_sensor import PMSA003I

def main(serial, i2c):
    """ Main function that collects data from the sensors and sends it to the serial port. """
    co2_sensor = SCD40(i2c)
    temp_humidity_sensor = SHT45(i2c)
    voc_sensor = SGP40(i2c)
    pm_sensor = PMSA003I(i2c)

    while True:
        co2_value = co2_sensor.read_co2()
        temp_value, humidity_value = temp_humidity_sensor.read_temperature_humidity()
        voc_value = voc_sensor.read_voc()
        pm_values = pm_sensor.read_pm()

        serial.write(f"CO2: {co2_value} ppm, Temp: {temp_value} C, Humidity: {humidity_value} %, VOC: {voc_value} ppb, PM: {pm_values}")
        time.sleep(5)


i2c = I2C(0, scl=Pin(22), sda=Pin(21))
serial = Serial(0, baudrate=115200)

if __name__ == "__main__":
    main(serial, i2c)
