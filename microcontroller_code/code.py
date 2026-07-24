import asyncio

from hardware.led import LED
from hardware.feathers3neo import FeatherS3Neo
from hardware.button import Button
from hardware.clock import Clock
from hardware.logger import DataLogger, EventLogger, SDSink, ConsoleSink, TCPSink
from hardware.sd_card_manager import SDCardManager
from air_quality_sensor import AirQualitySensor
from network_manager import WifiManager
from aqs_settings import load_settings

def main():  
    # Initialize FeatherS3Neo hardware interface
    feather = FeatherS3Neo()

    # Load settings
    cfg = load_settings()

    # Initialize Objects
    led             = LED(feather.matrix, feather.pixel, feather.blue_led, feather.pixel_power, cfg)
    wifi_manager    = WifiManager(cfg)
    clock           = Clock(feather.i2c, feather.internal_rtc)
    sd_manager      = SDCardManager(feather.spi, feather.cs_pin)
    sinks           = [SDSink(cfg), 
                       ConsoleSink(cfg), 
                       TCPSink(wifi_manager, cfg)]
    data_logger     = DataLogger(sinks, led, clock, cfg)
    event_logger    = EventLogger(led, clock)
    button          = Button(feather.button_pin)

    # Indicate system is ready
    feather.startup_message(clock.battery_low)
    led.spiral()

    try:
        with AirQualitySensor(led, feather.i2c, data_logger, event_logger, 
                              button, clock, cfg) as air_quality:
            
            try:
                asyncio.run(air_quality.run())

            except KeyboardInterrupt:
                air_quality.event_logger.warning("Program interrupted by user.")

            except Exception as e:
                air_quality.event_logger.error(f"Error: {e}")
                raise RuntimeError(f"Error: {e}")

    except RuntimeError as e:
        print(f"A runtime error occurred. {e}")
        sd_manager.unmount()
        led.continuous_error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        sd_manager.unmount()
        led.continuous_error_blink()

    finally:
        sd_manager.unmount()

if __name__ == "__main__":
    main()
