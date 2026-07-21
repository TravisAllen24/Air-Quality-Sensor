import time

from utils import rgb_color_wheel
from hardware.feathers3neo import FeatherS3Neo
from hardware.led import LED

feather = FeatherS3Neo()
led = LED(feather.matrix, feather.pixel, feather.blue_led, feather.pixel_power, brightness=0.2)
for _ in range(3):
    led.log_data_blink()

led.spiral(duration=10)


class MatrixAnimation:

    def __init__(self, matrix, anim_type, trail_length):

        # List of animation shapes by pixel index
        # Pixel 0 is Top Left, pixels increase vertically by row
        # Feel free to make your own shapes!
        self.matrix_display_shapes = {
            "square": [0,1,2,3,4,5,6,13,20,27,34,41,48,47,46,45,44,43,42,35,28,21,14,7],
               "spiral": [24,25,32,31,30,23,16,17,18,25,32,39,38,37,36,29,22,15,8,9,10,11,12,19,26,33,40,47,46,45,44,43,42,35,28,21,14,7,0,1,2,3,4,5,6,13,20,27,34,41,48,47,46,45,44,43,42,35,28,21,14,7,8,9,10,11,12,19,26,33,40,39,38,37,36,29,22,15,16,17,18,25,32,31,30,23,24,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        }

        # Initialiation error status
        self.error = False

        if anim_type not in self.matrix_display_shapes:
            print(f"** '{anim_type}' not found in list of shapes!\n** Animation halted!")
            self.error = True
        elif trail_length < 1 or trail_length > 20:
            print(f"** trail_length cannot be {trail_length}. Please pick a value between 1 and 20!\n** Animation halted!")
            self.error = True

        if not self.error:
            self.matrix = matrix
            self.anim_type = anim_type
            self.trail_length = trail_length + 1

            # Create the trail list base don the length of the trail
            self.anim_trail = [x for x in range(0, -self.trail_length,-1)]

            # Create a reference to the selected animation list
            self.current_anim = self.matrix_display_shapes[self.anim_type]

    def get_alpha(self):
        return 0.2 * (self.trail_length-1)

    def inc_anim_index(self, index):
        self.anim_trail[index] += 1
        if self.anim_trail[index] == len(self.current_anim):
            self.anim_trail[index] = 0

    def get_anim_index(self, index ):
        return self.current_anim[self.anim_trail[index]]

    def animate(self, r, g, b):
        if not self.error:
            alpha = self.get_alpha()
            for index in range(self.trail_length):
                if self.anim_trail[index] > -1:
                    (r2, g2, b2) = r * alpha, g * alpha, b * alpha
                    if self.get_anim_index(index) > -1:
                        self.matrix[ self.get_anim_index(index) ] = (r2, g2, b2)
                    alpha = alpha - 0.2 if alpha > 0.2 else 0

                self.inc_anim_index(index)


# Initialise the matrix animation class, passing it the matrix, the animation shape name, and the trail length
# You can use this class to make pretty trail based shape animations
matrix_anim = MatrixAnimation(feather.matrix, 'spiral', 7)


def spiral(next_color_step = 0.01, NEXT_COL = 0.01):

    color_index = 0
    while True:
        if time.monotonic() > NEXT_COL + next_color_step:
            color_index += 1
            # Get the R,G,B values of the next color
            r,g,b = rgb_color_wheel( color_index )

            NEXT_COL = time.monotonic()

        matrix_anim.animate(r, g, b)
        # Sleep for 40ms so the animation cycle isn't too fast
        time.sleep(0.04)

if __name__ == "__main__":
    feather.startup_message()
    spiral()
