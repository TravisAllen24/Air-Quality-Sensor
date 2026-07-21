import asyncio
import os

from hardware.led import LED
from hardware.feathers3neo import FeatherS3Neo
from hardware.button import Button
from hardware.clock import Clock
from hardware.logger import DataLogger, EventLogger, SDSink, ConsoleSink, TCPSink
from hardware.sd_card_manager import SDCardManager
from air_quality_sensor import AirQualitySensor
from aqs_settings import load_settings, get
from network_manager import WifiManager

def main():

    # Initialize FeatherS3Neo hardware interface
    feather = FeatherS3Neo()
    feather.startup_message()

    # Load settings
    cfg = load_settings()

    # Initialize Objects
    led = LED(brightness=get(cfg, "led.brightness", 0.2), matrix=feather.matrix, 
              pixel=feather.pixel, blue_led=feather.blue_led, pixel_power=feather.pixel_power)
    
    led.spiral()

    wifi_manager = WifiManager(ssid=os.getenv("CIRCUITPY_WIFI_SSID"), 
                               password=os.getenv("CIRCUITPY_WIFI_PASSWORD"))

    try:
        wifi_manager.connect()
    except Exception as e:
        print(f"Wi-Fi connection failed: {e}")

    sinks = [SDSink(), ConsoleSink(), TCPSink(wifi_manager)]

    sd_manager = SDCardManager()
    data_logger = DataLogger(led = led, sinks=sinks, clock=Clock(feather.i2c, feather.internal_rtc))
    event_logger = EventLogger(led=led, clock=Clock(feather.i2c, feather.internal_rtc))

    button = Button(feather.button_pin)
    clock = Clock(feather.i2c, feather.internal_rtc)


    try:
        # Initialize AirQualitySensor with LED
        with AirQualitySensor(led, feather.i2c, data_logger, event_logger, button, clock) as air_quality:

            try:
                asyncio.run(air_quality.run())

            except KeyboardInterrupt:
                air_quality.event_logger.warning("Program interrupted by user.")

            except Exception as e:
                air_quality.event_logger.error(f"Error: {e}")
                raise RuntimeError(f"Error: {e}")

    except RuntimeError as e:
        print(f"A runtime error occurred. {e}")
        led.continuous_error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.continuous_error_blink()

    finally:
        sd_manager.unmount()

if __name__ == "__main__":
    main()
