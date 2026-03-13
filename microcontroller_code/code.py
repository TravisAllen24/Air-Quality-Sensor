
import asyncio

from led import LED
from button import Button
from sd_logger import SDLogger
from air_quality import AirQuality


if __name__ == "__main__":
    # --- Init objects ---
    led = LED()
    button = Button()

    try:
        sd_logger = SDLogger()
        air_quality = AirQuality(led, button, sd_logger)

        try:
            asyncio.run(air_quality.run())

        except KeyboardInterrupt:
            print("Program interrupted by user.")
            sd_logger.log_info(air_quality.now, "Program interrupted by user.")
            air_quality.safe_shutdown()

        except Exception as e:
            print(f'Error: {e}')
            sd_logger.log_info(air_quality.now, f"Error: {e}")
            air_quality.safe_shutdown()
            led.error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.error_blink()
