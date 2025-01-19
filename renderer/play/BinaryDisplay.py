
# Simple module to store Solarized color schemes
BASE03 = "#002b36"
BASE02 = "#073642"
BASE01 = "#586e75"
BASE00 = "#657b83"
BASE0 = "#839496"
BASE1 = "#93a1a1"
BASE2 = "#eee8d5"
BASE3 = "#fdf6e3"
YELLOW = "#b58900"
ORANGE = "#cb4b16"
RED = "#dc322f"
MAGENTA = "#d33682"
VIOLET = "#6c71c4"
BLUE = "#268bd2"
CYAN = "#2aa198"
GREEN = "#859900"


class SolarizedDark():
    BG = BASE03
    BG_HIGHLIGHT = BASE02
    PRIMARY = BASE0
    SECONDARY = BASE01
    EMPHASIZED = BASE1
    # In both Dark and Light
    YELLOW = YELLOW
    ORANGE = ORANGE
    RED = RED
    MAGENTA = MAGENTA
    VIOLET = VIOLET
    BLUE = BLUE
    CYAN = CYAN
    GREEN = GREEN

class SolarizedLight(SolarizedDark):
    BG = BASE3
    BG_HIGHLIGHT = BASE2
    PRIMARY = BASE00
    SECONDARY = BASE1
    EMPHASIZED = BASE01

"""
Manim Binary Number Display
by Bryce Corbitt
"""
from manim import *
import numpy as np
Scheme = SolarizedDark

default_font='Apercu Mono Pro'  # You probably want to change this to a free font

# More so just Mutable Text
class Digit(VMobject):
    @property
    def digit_str(self):
        return str(self.value)

    def __init__(self, value, font=default_font, color=Scheme.PRIMARY, **kwargs):
        VMobject.__init__(self, **kwargs)
        self.value = value
        self.font = font
        self.digit_color = color
        self.digit_text = Text(text=self.digit_str, font=self.font, color=self.digit_color)
        self.add(self.digit_text)
    
    def set_value(self, val, run_time=.15) -> Animation:
        self.value = val
        pop_scale = 1.5  # Scale of text when temporarily growing in animation
        new_text = Text(text=self.digit_str, font=self.font, color=self.digit_color)
        new_text.move_to(self.digit_text)
        anim = Succession(
            ApplyMethod(self.digit_text.become, new_text, run_time=0), # Turn old text into new text
            ScaleInPlace(self.digit_text, pop_scale, run_time=run_time/3),
            Wait(run_time/3),
            ScaleInPlace(self.digit_text, 1/pop_scale, run_time=run_time/3) # Shrink back down to original size
        )
        return anim


# Adds two 2^{power} above digit
class BinaryDigit(Digit):
    @property
    def power_str(self):
        return rf"2^{self.power}"
    def __init__(self, value=0, power=0, digit_color=Scheme.EMPHASIZED, power_color=Scheme.SECONDARY, **kwargs):
        kwargs['color'] = digit_color
        super().__init__(value, **kwargs)
        self.power = power
        self.power_color = power_color
        self.power_text = MathTex(self.power_str, font=self.font, tex_to_color_map={self.power_str: self.power_color})
        self.centered_height = np.array((0.0, self.power_text.height, 0.0))

        # Orient power above digit and rotate slightly
        self.add(self.power_text)
        self.power_text.shift(RIGHT*.15 + UP*.75)
        self.power_text.rotate(np.radians(15))


# Adds "=" sign to left of digit, and causes number to remain aligned
class EqualsDigit(Digit):
    def __init__(self, value, **kwargs):
            super().__init__(value, **kwargs)
            self.equals_sym = Text(text='=', font=self.font, color=self.digit_color, size=1.5)
            self.digit_text.next_to(self.equals_sym, RIGHT, buff=.5)
            self.add(self.equals_sym)

    # Same as Digit.set_value, but result is left aligned relative to equals sign
    def set_value(self, val, run_time=.15) -> Succession:
        self.value = val
        pop_scale = 1.5
        new_text = Text(text=self.digit_str, font=self.font, color=self.digit_color)

        # This is the only line that changed
        new_text.next_to(self.equals_sym, RIGHT, buff=.5)

        anim = Succession(
            ApplyMethod(self.digit_text.become, new_text, run_time=0),
            ScaleInPlace(self.digit_text, pop_scale, run_time=run_time/3),
            Wait(run_time/3),
            ScaleInPlace(self.digit_text, 1/pop_scale, run_time=run_time/3)
        )
        return anim


# Everything together as a binary number
class BinaryNumber(VMobject):
    def _validate_data(self, data=None):
        if data is None:
            data = [0]*self.num_digits
        elif isinstance(data, int):
            data = [int(ch) for ch in bin(data).replace('0b', '')]
        elif isinstance(data, str):
            data = [int(ch) for ch in data.replace('0b', '')]
        elif isinstance(data, list):
            pass
        else:
            raise ValueError("BinaryNumber data must be string of bits or array of bit values")
        if len(data) > self.num_digits:  # Truncate
            data = data[:self.num_digits]
        elif len(data) < self.num_digits: # Pad with zeros
            data = [0]*(self.num_digits-len(data)) + data
        return data
    
    # Get binary number in base 10. 
    def base10_val(self, bit_data):
        b10 = 0
        for i in range(len(bit_data)):
            b10 += bit_data[i]*2**(len(bit_data)-1-i+self.starting_power)
        if isinstance(b10, float) and float.is_integer(b10):
            b10 = int(b10)
        return b10

    def __init__(self, num_digits, data=None, starting_power=0, digit_params: dict = None, **kwargs):
        VMobject.__init__(self, **kwargs)
        self.digit_params = digit_params
        self.num_digits = num_digits
        self.data = self._validate_data(data)
            
        self.starting_power = starting_power
        self.digit_params = digit_params
        self.digits = VGroup()  # Define digits

        # Add digits in reverse order so that values array reflects ordering on in animation
        for i in range(num_digits):
            if self.digit_params is not None:
                dg = BinaryDigit(value=self.data[i], power=starting_power+num_digits-1-i, **digit_params)
            else:
                dg = BinaryDigit(value=self.data[i], power=starting_power+num_digits-1-i)
            self.digits.add(dg)

        self.result_text = EqualsDigit(value=self.base10_val(self.data))
        self.digits.arrange(RIGHT)
        self.digits.shift(self.digits[0].centered_height)  # Centers digits vertically on screen
        self.digits.shift(LEFT) # Brings base 10 value closer to center
        self.add(self.digits)

        self.result_text.next_to(self.digits, RIGHT)
        self.add(self.result_text)
    
    def set_value(self, data, run_time=.15):
        data = self._validate_data(data)
        if data == self.data:
            # Manim would throw error at render time for returning Null or an empty animation
            raise ValueError("Data passed to set_value is identical to current state")
        digit_anims = []
        for i in range(len(self.data)):
            if self.data[i] != data[i]:
                digit_anims.append(self.digits[i].set_value(data[i], run_time=run_time))
        digit_anims.append(self.result_text.set_value(self.base10_val(data), run_time=run_time))

        async_anims = []
        # Following code assumes AnimationGroup for each digit is same length (wich it should be)
        for i in range(len(digit_anims[0].animations)):
            if isinstance(digit_anims[0].animations[i], Wait):  # If a Wait, we know the rest of them will be Wait, so only add one
                async_anims.append(digit_anims[0].animations[i])
            else:
                # Any other Animations at same index will be combined into an AnimationGroup to be run at the same time
                agroup = AnimationGroup(*[a.animations[i] for a in digit_anims]) 
                async_anims.append(agroup)

        self.data = data # Don't forget to update the bit values
        return Succession(*async_anims)


# Sample Scene for testing
class TestScene(Scene):
    def construct(self):
        self.camera.background_color = Scheme.BG

        num = BinaryNumber(8) # Binary Number with 8 digits (default value of 0)
        self.play(DrawBorderThenFill(num))

        change_time = lambda x: max(1 / np.power(2, np.log2(x)), 3/config['frame_rate'])
        for i in range(1, 33): # Transitions start at 1, and end at 32
            pause = change_time(i)
            self.play(num.set_value(bin(i), run_time=pause))
            self.wait(pause*2)

        self.wait(2)
        self.play(num.set_value(255))
        self.wait(1.5)
        self.play(num.set_value('10101010'))
        self.wait(1.5)
        self.play(num.set_value('01010101'))
        self.wait(1)

        self.play(Uncreate(num))