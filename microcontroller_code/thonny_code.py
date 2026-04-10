import asyncio

from led import LED
from button import Button
from air_quality import AirQuality


if __name__ == "__main__":
    # --- Init objects ---
    led = LED()
    button = Button()

    try:
        air_quality = AirQuality(led, button, logger=None)

        try:
            asyncio.run(air_quality.run())

        except KeyboardInterrupt:
            print("Program interrupted by user.")
            air_quality.safe_shutdown()

        except Exception as e:
            print(f'Error: {e}')
            air_quality.safe_shutdown()
            led.error_blink()

    except Exception as e:
        print(f"Initialization error: {e}")
        led.error_blink()
