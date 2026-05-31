import board # type: ignore
import storage # type: ignore
import sdcardio # type: ignore
import rtc # type: ignore

from clock import Clock
from utils import format_value, c_to_f

class SDLogger:
    def __init__(self, i2c, led, should_print: bool = True, print_in_csv_format = False, temp_unit: str = "C"):
        # Update system clock
        self.system_rtc = rtc.RTC()
        self.clock = Clock(i2c)
        self._sync_system_rtc()
        """Mount SD card and prepare for logging."""
        self.led = led
        self.temp_unit = temp_unit
        # Set up SPI and SD card
        spi = board.SPI()
        cs_pin=board.D10
        mount_path="/sd"
        self.sdcard = sdcardio.SDCard(spi, cs_pin)
        self.mount_path = mount_path
        # Mount SD card
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, self.mount_path)
        self.file_path = None
        self.active = False
        self.should_print = should_print
        self.print_in_csv_format = print_in_csv_format


    # In your SDLogger.__init__, after setting up self.clock:
    def _sync_system_rtc(self):
        """Sync CircuitPython's built-in RTC from your external RTC module."""
        now = self.clock.datetime  # your Clock's raw datetime tuple/struct
        self.system_rtc.datetime = now


    def log_info(self, msg: str, color: str|None = None):
        """Log an info or error message to a separate log file on the SD card,
        and optionally print to console and blink LED."""

        log_file = f"{self.mount_path}/info.log"
        if self.should_print:
            print(f"{self.clock.now}: {msg}")
        try:
            with open(log_file, "a") as f:
                f.write(f"{self.clock.now}: {msg}\n")
        except Exception as e:
            # If logging fails, print to console as fallback
            print(f"SDLogger log_info error: {e}")

        if color:
            self.led.blink_once(color)


    def start_new_log(self):
        """Start a new log file with datetime in filename."""
        dt_sanitised = self.clock.now.replace(":", "-").replace(" ", "_")
        self.file_path = f"{self.mount_path}/log_{dt_sanitised}.csv"
        with open(self.file_path, "w") as f:
            f.write("timestamp,co2 (ppm),temp ({u}),humidity (%),voc_raw,voc_index,pm10 (ug/m3),pm25 (ug/m3),pm100 (ug/m3)\n".format(u=self.temp_unit))
        self.active = True


    def stop_log(self):
        self.active = False
        self.file_path = None


    def _convert_temp(self, temp_c):
        """Convert temperature based on temp_unit setting."""
        if self.temp_unit == "F":
            return c_to_f(temp_c)
        return temp_c


    def log_data(self, co2_value: int|str|None, temp_value: float|str|None, humidity_value: float|str|None,
                       voc_raw: int|str|None, voc_index: int|str|None, nox_raw: int|str|None, nox_index: int|str|None, pm:dict|None):
        if not self.active or not self.file_path:
            return
        temp = self._convert_temp(temp_value)
        pm10 = pm.get("pm10 env") if pm else None
        pm25 = pm.get("pm25 env") if pm else None
        pm100 = pm.get("pm100 env") if pm else None
        with open(self.file_path, "a") as f:
            f.write(f"{self.clock.now},{co2_value},{temp},{humidity_value},{voc_raw},{voc_index},{nox_raw},{nox_index},{pm10},{pm25},{pm100}\n")

        if self.led:
            self.led.blink_once('blue')


    def print_sensor_data(self, temp_c, humidity, dew_point_c, co2, voc_raw, voc_index, nox_raw, nox_index, pm10, pm25, pm100):
        """Build and print a formatted sensor data message."""
        if not self.should_print:
            return
        temp = format_value(self._convert_temp(temp_c), 2)
        dp = format_value(self._convert_temp(dew_point_c), 2)
        if self.print_in_csv_format:
            print(f"{self.clock.now},{co2},{temp},{dp},{humidity},{voc_raw},{voc_index},{nox_raw},{nox_index},{pm10},{pm25},{pm100}")

        else:
            msg = ("T: {} {} RH: {}% -> DP: {} {} | CO2: {} ppm | "
                   "VOC Raw: {} VOC Index: {} | NOx Raw: {} NOx Index: {} | PM10: {} PM2.5: {} PM1.0: {}".format(
                        temp, self.temp_unit,
                        format_value(humidity, 2),
                        dp, self.temp_unit,
                        format_value(co2),
                        format_value(voc_raw),
                        format_value(voc_index),
                        format_value(nox_raw),
                        format_value(nox_index),
                        format_value(pm100),
                        format_value(pm25),
                        format_value(pm10),
            ))
            self.print_with_timestamp(msg)


    def unmount(self):
        """Unmount the SD card safely."""
        storage.umount(self.mount_path)


    def print_with_timestamp(self, msg: str):
        """Print a message with RTC timestamp."""
        if self.should_print:
            print(f"RTC {self.clock.now} | {msg}")
