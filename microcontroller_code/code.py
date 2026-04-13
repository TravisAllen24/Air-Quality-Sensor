import asyncio

from led import LED
from air_quality_sensor import AirQualitySensor
from microcontroller_code.aqs_settings import load_settings, get

def main():
    # Load settings
    cfg = load_settings()

    # Initialize LED
    led = LED(brightness=get(cfg, "led.brightness", 0.2))

    try:
        # Initialize AirQualitySensor with LED
        with AirQualitySensor(led) as air_quality:

            try:
                asyncio.run(air_quality.run())

            except KeyboardInterrupt:
                air_quality.sd_logger.log_info("Program interrupted by user.", color='yellow')

            except Exception as e:
                air_quality.sd_logger.log_info(f"Error: {e}")
                raise RuntimeError

    except RuntimeError as e:
        print(f"A runtime error occurred. {e}")
        led.error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.error_blink()

if __name__ == "__main__":
    main()
