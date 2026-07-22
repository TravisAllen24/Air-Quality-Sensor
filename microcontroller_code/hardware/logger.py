from aqs_settings import get, load_settings

class TCPSink:
    def __init__(self, wifi_manager, temp_unit="C"):
        self.wifi_manager = wifi_manager
        self.temp_unit = temp_unit

    def start(self):
        if self.wifi_manager.is_connected():
            self.wifi_manager.open_tcp_connection()

    def write_data(self, data: "AQSData"): # type: ignore
        if self.wifi_manager.is_connected():
            self.wifi_manager.send_data(data)

    def stop(self):
        if self.wifi_manager.is_connected():
            self.wifi_manager.close_tcp_connection()


class ConsoleSink:
    def __init__(self, print_in_csv_format=False, temp_unit="C"):
        self.print_in_csv_format = print_in_csv_format
        self.temp_unit = temp_unit

    def write_data(self, data: "AQSData"): # type: ignore
        """Build and print a formatted sensor data message."""
        if self.print_in_csv_format:
            print(data)

        else:
            print(data.format_to_print(self.temp_unit))


class SDSink:
    def __init__(self, temp_unit="C"):
        self.temp_unit = temp_unit

    def start_new_log(self, dt_sanitised):
        """Start a new log file with datetime in filename."""
        self.file_path = f"/sd/log_{dt_sanitised}.csv"
        with open(self.file_path, "w") as f:
            f.write("timestamp,temp ({u}),humidity (%),co2 (ppm),voc_raw,voc_index,nox_raw,nox_index,pm10 (ug/m3),pm25 (ug/m3),pm100 (ug/m3)\n".format(u=self.temp_unit))

    def stop_log(self):
        self.file_path = None

    def write_data(self, data: "AQSData"): # type: ignore
        if not self.file_path:
            return
        with open(self.file_path, "a") as f:
            f.write(f"{data}\n")


class DataLogger:
    def __init__(self, sinks: list, led, clock):
        aqs_settings = load_settings()

        self.sinks = sinks
        self.led = led
        self.clock = clock
        self.print_in_csv_format = get(aqs_settings, "sd_logger.print_in_csv_format", False)
        self.temp_unit = get(aqs_settings, "sd_logger.temp_unit", "C")

        self.startup()

    def startup(self):
        for sink in self.sinks:
            if isinstance(sink, TCPSink):
                sink.start()

    def shutdown(self):
        for sink in self.sinks:
            if isinstance(sink, TCPSink):
                sink.stop()
            if isinstance(sink, SDSink):
                sink.stop_log()
        
    def start_new_log(self):
        for sink in self.sinks:
            if isinstance(sink, SDSink):
                sink.start_new_log(self.clock.internal_now.replace(":", "-").replace(" ", "_"))
            
        self.led.start_log_blink()

    def stop_log(self):
        for sink in self.sinks:
            if isinstance(sink, SDSink):
                sink.stop_log()
            
        self.led.stop_log_blink()

    def ensure_temp_unit(self, data: "AQSData") -> "AQSData": # type: ignore
        if self.temp_unit == "F":
            data = data.convert_to_fahrenheit()
        return data

    def log_data(self, data: "AQSData"): # type: ignore
        """Log data to all sinks."""
        data = self.ensure_temp_unit(data)

        for sink in self.sinks:
            if isinstance(sink, SDSink):
                sink.write_data(data)

        self.led.log_data_blink()

    def send_data(self, data: "AQSData"): # type: ignore
        data = self.ensure_temp_unit(data)

        for sink in self.sinks:
            if isinstance(sink, ConsoleSink):
                sink.write_data(data)
            elif isinstance(sink, TCPSink):
                sink.write_data(data)
    

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
