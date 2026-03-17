


import board # type: ignore
import busio # type: ignore
import storage # type: ignore
import adafruit_sdcard # type: ignore
import digitalio # type: ignore

from rtc import RTC

class SDLogger:
    def __init__(self, i2c, led, cs_pin=board.D10, spi=None, mount_path="/sd", should_print: bool = True):
        """Mount SD card and prepare for logging."""
        self.rtc = RTC(i2c)
        self.led = led
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
        self.should_print = should_print

    def log_info(self, msg: str, color: str|None = None):
        """Log an info or error message to a separate log file on the SD card,
        and optionally print to console and blink LED."""

        log_file = f"{self.mount_path}/info.log"
        if self.should_print:
            print(f"{self.rtc.now}: {msg}")
        try:
            with open(log_file, "a") as f:
                f.write(f"{self.rtc.now}: {msg}\n")
        except Exception as e:
            # If logging fails, print to console as fallback
            print(f"SDLogger log_info error: {e}")

        if color:
            self.led.blink_once(color)


    def start_new_log(self):
        """Start a new log file with datetime in filename."""
        dt_sanitised = self.rtc.now.replace(":", "-").replace(" ", "_")
        self.file_path = f"{self.mount_path}/log_{dt_sanitised}.csv"
        with open(self.file_path, "w") as f:
            f.write("timestamp,co2,temp,humidity,voc_raw,voc_index,pm10,pm25,pm100\n")
        self.active = True

    def stop_log(self):
        self.active = False
        self.file_path = None

    def log_data(self, co2_value: int|str|None, temp_value: float|str|None, humidity_value: float|str|None,
                       voc_raw: int|str|None, voc_index: int|str|None, pm:dict|None):
        if not self.active or not self.file_path:
            return
        pm10 = pm.get("pm10 env") if pm else None
        pm25 = pm.get("pm25 env") if pm else None
        pm100 = pm.get("pm100 env") if pm else None
        with open(self.file_path, "a") as f:
            f.write(f"{self.rtc.now},{co2_value},{temp_value},{humidity_value},{voc_raw},{voc_index},{pm10},{pm25},{pm100}\n")

        if self.led:
            self.led.blink_once('blue')

    def unmount(self):
        """Unmount the SD card safely."""
        storage.umount(self.mount_path)

    def print_with_timestamp(self, msg: str):
        """Print a message with RTC timestamp."""
        print(f"RTC {self.rtc.now} | {msg}")