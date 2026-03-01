


import board
import busio
import storage
import adafruit_sdcard
import digitalio
import os

class SDLogger:
    """Handles logging operations, including writing data to an SD card."""
    def __init__(self, cs_pin=board.D10, spi=None, mount_path="/sd", filename="log.csv"):
        """Mount SD card and prepare for logging."""
        # Set up SPI and SD card
        if spi is None:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.cs = digitalio.DigitalInOut(cs_pin)
        self.sdcard = adafruit_sdcard.SDCard(spi, self.cs)
        self.mount_path = mount_path
        self.filename = filename
        # Mount SD card
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, self.mount_path)
        # Create file with header if it doesn't exist
        file_path = self.mount_path + "/" + self.filename
        if self.filename not in os.listdir(self.mount_path):
            with open(file_path, "a") as f:
                f.write("timestamp,co2,temp,humidity,voc_raw,pm10,pm25,pm100\n")

    def log_data_to_sd(self, time, co2_value, temp_value, humidity_value, voc_raw, pm):
        # Write a line of CSV data to the SD card
        pm10 = pm.get("pm10 env") if pm else None
        pm25 = pm.get("pm25 env") if pm else None
        pm100 = pm.get("pm100 env") if pm else None
        file_path = self.mount_path + "/" + self.filename
        with open(file_path, "a") as f:
            f.write(f"{time},{co2_value},{temp_value},{humidity_value},{voc_raw},{pm10},{pm25},{pm100}\n")