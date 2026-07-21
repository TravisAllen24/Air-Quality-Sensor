import asyncio
import os

from hardware.led import LED
from hardware.feathers3neo import FeatherS3Neo
from hardware.sd_logger import SDLogger
from hardware.button import Button
from air_quality_sensor import AirQualitySensor
from aqs_settings import load_settings, get
from network_manager import WifiManager

def main():
    wifi_manager = WifiManager(ssid=os.getenv("CIRCUITPY_WIFI_SSID"), 
                               password=os.getenv("CIRCUITPY_WIFI_PASSWORD"))

    try:
        wifi_manager.connect()
    except Exception as e:
        print(f"Wi-Fi connection failed: {e}")

    # Load settings
    cfg = load_settings()

    # Initialize FeatherS3Neo hardware interface
    feather = FeatherS3Neo()

    # Initialize Objects
    led = LED(brightness=get(cfg, "led.brightness", 0.2), matrix=feather.matrix, 
              pixel=feather.pixel, blue_led=feather.blue_led, pixel_power=feather.pixel_power)
    
    sd_logger = SDLogger(i2c=feather.i2c, led=led, internal_rtc=feather.internal_rtc, 
                         should_print=get(cfg, "sd_logger.should_print", True), 
                         print_in_csv_format=get(cfg, "sd_logger.print_in_csv_format", False), 
                         temp_unit=get(cfg, "sd_logger.temp_unit", "C"))
    
    button = Button(feather.button_pin)

    feather.startup_message()
    led.spiral()

    try:
        # Initialize AirQualitySensor with LED
        with AirQualitySensor(led, feather.i2c, sd_logger, button) as air_quality:

            try:
                asyncio.run(air_quality.run())

            except KeyboardInterrupt:
                air_quality.sd_logger.warning("Program interrupted by user.")

            except Exception as e:
                air_quality.sd_logger.error(f"Error: {e}")
                raise RuntimeError

    except RuntimeError as e:
        print(f"A runtime error occurred. {e}")
        led.continuous_error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.continuous_error_blink()

if __name__ == "__main__":
    main()
