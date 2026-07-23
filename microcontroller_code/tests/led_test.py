import time

from utils import rgb_color_wheel
from hardware.feathers3neo import FeatherS3Neo
from hardware.led import LED

feather = FeatherS3Neo()
# feather.set_pixel_power(False)
led = LED(feather.matrix, feather.pixel, feather.blue_led, feather.pixel_power, brightness=0.2)

led.all_off()
time.sleep(1)
led.blue_blink(blinks=5)

led.all_on(color='red')
time.sleep(1)
led.all_off()

for _ in range(3):
    led.log_data_blink()
    
led.blink(color="red", blinks=5)
    
led.spiral(duration=10)
