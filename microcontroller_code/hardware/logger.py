from utils import format_value
from aqs_settings import get, load_settings
from aqs_data import AQSData


class TCPSink:
    def __init__(self, wifi_manager, temp_unit="C"):
        self.wifi_manager = wifi_manager
        self.temp_unit = temp_unit

    def start_logging(self):
        if self.wifi_manager.is_connected():
            self.wifi_manager.open_tcp_connection()

    def send_data(self, data: AQSData):
        if self.wifi_manager.is_connected():
            self.wifi_manager.send_data(f"$AQS,{data.datetime},{data.temp},{data.humidity},{data.dp},{data.co2},{data.voc_raw},{data.voc_index},{data.nox_raw},{data.nox_index},{data.pm100},{data.pm25},{data.pm10}")

    def stop_logging(self):
        if self.wifi_manager.is_connected():
            self.wifi_manager.close_tcp_connection()


class ConsoleSink:
    def __init__(self, print_in_csv_format=False, temp_unit="C"):
        self.print_in_csv_format = print_in_csv_format
        self.temp_unit = temp_unit

    def print_data(self, data: AQSData):
        """Build and print a formatted sensor data message."""
        if self.print_in_csv_format:
            print(f"$AQS,{data.datetime},{data.temp},{data.humidity},{data.dp},{data.co2},{data.voc_raw},{data.voc_index},{data.nox_raw},{data.nox_index},{data.pm100},{data.pm25},{data.pm10}")

        else:
            msg = ("RTC {} | T: {} {} RH: {}% -> DP: {} {} | CO2: {} ppm | "
                   "VOC Raw: {} VOC Index: {} | NOx Raw: {} NOx Index: {} | PM10: {} PM2.5: {} PM1.0: {}".format(
                        data.datetime,
                        format_value(data.temp, 2), self.temp_unit,
                        format_value(data.humidity, 2),
                        format_value(data.dp, 2), self.temp_unit,
                        format_value(data.co2),
                        format_value(data.voc_raw),
                        format_value(data.voc_index),
                        format_value(data.nox_raw),
                        format_value(data.nox_index),
                        format_value(data.pm100),
                        format_value(data.pm25),
                        format_value(data.pm10),
            ))
            print(msg)


class SDSink:
    def __init__(self, temp_unit="C"):
        self.temp_unit = temp_unit

    def start_new_log(self, dt_sanitised):
        """Start a new log file with datetime in filename."""
        self.file_path = f"/sd/log_{dt_sanitised}.csv"
        with open(self.file_path, "w") as f:
            f.write("timestamp,temp ({u}),humidity (%),co2 (ppm),voc_raw,voc_index,nox_raw,nox_index,pm10 (ug/m3),pm25 (ug/m3),pm100 (ug/m3)\n".format(u=self.temp_unit))
        self.active = True

    def stop_log(self):
        self.active = False
        self.file_path = None

    def log_data(self, data: AQSData):
        if not self.active or not self.file_path:
            return
        pm10 = data.pm10 if data.pm10 is not None else None
        pm25 = data.pm25 if data.pm25 is not None else None
        pm100 = data.pm100 if data.pm100 is not None else None
        with open(self.file_path, "a") as f:
            f.write(f"{data.datetime},{data.temp},{data.humidity},{data.co2},{data.voc_raw},{data.voc_index},{data.nox_raw},{data.nox_index},{pm10},{pm25},{pm100}\n")


class DataLogger:
    def __init__(self, sinks: list, led, clock):
        aqs_settings = load_settings()

        self.sinks = sinks
        self.sd_sink = next((sink for sink in sinks if isinstance(sink, SDSink)), None) # ???
        self.led = led
        self.clock = clock
        self.print_in_csv_format = get(aqs_settings, "sd_logger.print_in_csv_format", False)
        self.temp_unit = get(aqs_settings, "sd_logger.temp_unit", "C")
    
    def start_new_log(self):
        for sink in self.sinks:
            if isinstance(sink, TCPSink):
                sink.start_logging()
            if isinstance(sink, SDSink):
                sink.start_new_log(self.clock.internal_now.replace(":", "-").replace(" ", "_"))
            
        self.led.start_log_blink()

    def stop_log(self):
        for sink in self.sinks:
            if isinstance(sink, TCPSink):
                sink.stop_logging()
            if isinstance(sink, SDSink):
                sink.stop_log()
            
        self.led.stop_log_blink()

    def ensure_temp_unit(self, data: AQSData) -> AQSData:
        if self.temp_unit == "F":
            data = data.convert_to_fahrenheit()
        return data

    def log_data(self, data: AQSData):
        """Log data to all sinks."""
        data = self.ensure_temp_unit(data)

        for sink in self.sinks:
            if isinstance(sink, SDSink):
                sink.log_data(data)

        self.led.log_data_blink()

    def send_data(self, data: AQSData):
        for sink in self.sinks:
            if isinstance(sink, ConsoleSink):
                sink.print_data(data)
            elif isinstance(sink, TCPSink):
                sink.send_data(data)
    

class EventLogger:
    def __init__(self, led, clock):
        self.led = led
        self.clock = clock

    def log_info(self, msg: str):
        """Log an info or error message to a separate log file on the SD card,
        and optionally print to console and blink LED."""

        log_file = "/sd/info.log"
        print(f"{self.clock.internal_now}: {msg}")
        try:
            with open(log_file, "a") as f:
                f.write(f"{self.clock.internal_now}: {msg}\n")
        except Exception as e:
            # If logging fails, print to console as fallback
            print(f"SDLogger log_info error: {e}")

    def debug(self, msg: str):
        self.log_info(f"DEBUG: {msg}")

    def warning(self, msg: str):
        self.log_info(f"WARNING: {msg}")
        self.led.warning_blink()

    def error(self, msg: str):
        self.log_info(f"ERROR: {msg}")
        self.led.error_blink()
