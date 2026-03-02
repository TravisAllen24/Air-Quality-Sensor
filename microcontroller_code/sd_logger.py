


import board
import busio
import storage
import adafruit_sdcard
import digitalio

class SDLogger:
    def __init__(self, cs_pin=board.D10, spi=None, mount_path="/sd"):
        """Mount SD card and prepare for logging."""
        # Set up SPI and SD card
        if spi is None:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.cs = digitalio.DigitalInOut(cs_pin)
        self.sdcard = adafruit_sdcard.SDCard(spi, self.cs)
        self.mount_path = mount_path
        # Mount SD card
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, self.mount_path)
        self.file_path = None
        self.active = False

    def log_info(self, timestamp, message):
        """Log an info or error message to a separate log file on the SD card."""
        log_file = f"{self.mount_path}/info.log"
        try:
            with open(log_file, "a") as f:
                f.write(f"{timestamp}: {message}\n")
        except Exception as e:
            # If logging fails, print to console as fallback
            print(f"SDLogger log_info error: {e}")

    def start_new_log(self, dt):
        """Start a new log file with datetime in filename."""
        # dt is a datetime object
        dt_str = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}_{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
        self.file_path = f"{self.mount_path}/log_{dt_str}.csv"
        with open(self.file_path, "w") as f:
            f.write("timestamp,co2,temp,humidity,voc_raw,pm10,pm25,pm100\n")
        self.active = True

    def stop_log(self):
        self.active = False
        self.file_path = None

    def log_data_to_sd(self, time, co2_value, temp_value, humidity_value, voc_raw, pm):
        if not self.active or not self.file_path:
            return
        pm10 = pm.get("pm10 env") if pm else None
        pm25 = pm.get("pm25 env") if pm else None
        pm100 = pm.get("pm100 env") if pm else None
        with open(self.file_path, "a") as f:
            f.write(f"{time},{co2_value},{temp_value},{humidity_value},{voc_raw},{pm10},{pm25},{pm100}\n")

    def unmount(self):
        """Unmount the SD card safely."""
        storage.umount(self.mount_path)