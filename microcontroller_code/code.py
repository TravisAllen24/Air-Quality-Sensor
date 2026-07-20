import asyncio

from hardware.led import LED
from hardware.feathers3neo import FeatherS3Neo
from air_quality_sensor import AirQualitySensor
from aqs_settings import load_settings, get
from hardware.sd_logger import SDLogger
from hardware.button import Button
from microcontroller_code.hardware import button

def main():
    # Load settings
    cfg = load_settings()

    # Initialize FeatherS3Neo hardware interface
    feather = FeatherS3Neo()
    i2c = feather.i2c
    internal_rtc = feather.internal_rtc
    matrix = feather.matrix
    pixel = feather.pixel
    blue_led = feather.blue_led
    btn_pin = feather.button_pin

    # Initialize Objects
    led = LED(brightness=get(cfg, "led.brightness", 0.2), matrix=matrix, pixel=pixel, blue_led=blue_led)
    sd_logger = SDLogger(i2c=i2c, led=led, internal_rtc=internal_rtc, should_print=get(cfg, "sd_logger.should_print", True), print_in_csv_format=get(cfg, "sd_logger.print_in_csv_format", False), temp_unit=get(cfg, "sd_logger.temp_unit", "C"))
    button = Button(btn_pin)

    try:
        # Initialize AirQualitySensor with LED
        with AirQualitySensor(led, i2c, sd_logger, button) as air_quality:

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
