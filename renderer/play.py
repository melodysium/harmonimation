from manim import *

class CreateCircle(Scene):
  def construct(self):
    circle = Circle()
    circle.set_fill(PINK, opacity=0.5)
    self.play(Create(circle))
  
class SquareToCircle(Scene):
  def construct(self):
        circle = Circle()  # create a circle
        circle.set_fill(PINK, opacity=0.5)  # set color and transparency

        square = Square()  # create a square
        square.rotate(PI / 4)  # rotate a certain amount

        self.play(Create(square))  # animate the creation of the square
        self.play(Transform(square, circle))  # interpolate the square into the circle
        self.play(FadeOut(square))  # fade out animation


class SquareAndCircle(Scene):
  def construct(self):
    circle = Circle()  # create a circle
    circle.set_fill(PINK, opacity=0.5)  # set the color and transparency

    square = Square()  # create a square
    square.set_fill(BLUE, opacity=0.5)  # set the color and transparency

    square.next_to(circle, RIGHT, buff=0.5)  # set the position
    self.play(Create(circle), Create(square))  # show the shapes on screen

  
class AnimatedSquareToCircle(Scene):
    def construct(self):
        circle = Circle()  # create a circle
        square = Square()  # create a square

        self.play(Create(square))  # show the square on screen
        self.play(square.animate.rotate(PI / 4))  # rotate the square
        self.play(
            ReplacementTransform(square, circle)
        )  # transform the square into a circle
        self.play(
            circle.animate.set_fill(PINK, opacity=0.5)
        )  # color the circle on screen

        lambda contact : contact['asdf']['qwer']

class DifferentRotations(Scene):
    def construct(self):
        left_square = Square(color=BLUE, fill_opacity=0.7).shift(2 * LEFT)
        right_square = Square(color=GREEN, fill_opacity=0.7).shift(2 * RIGHT)
        self.play(
            left_square.animate.rotate(PI), Rotate(right_square, angle=PI), run_time=2
        )
        self.wait()


#----------------------------------------------------------------------

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


#----------------------------------------------------------------


class Sort(Scene):
    def construct(self):
        group = VGroup()

        arr = [1, 4, 2, 8, 5, 7] 
        group = VGroup(*[CircledNumber(n) for n in arr])
        group.arrange(RIGHT)

        self.play(DrawBorderThenFill(group))
        self.wait()
        group.sort(submob_func=lambda x: x.number)
        self.play(
            group.animate.arrange(RIGHT),
            path_arc=2
        )
        self.wait()


class CircledNumber(VGroup):
    def __init__(self, number, **kwargs):
        super().__init__(**kwargs)
        self.number = number

        self.circle = Circle()
        self.add(self.circle)

        self.text = Text(str(self.number)).move_to(self.circle.get_center())
        self.add(self.text)


class CircleWithDots(VGroup):

    circle: Circle

    def __init__(self, **kwargs):
        self.circle = Circle()
        super().__init__(self.circle, **kwargs)

    def add_dots(self, num_dots: int) -> Animation:
        dots = [Dot(self.circle.point_from_proportion(step/num_dots))
                for step in range(num_dots)]
        return Succession(
                *[Create(dot) for dot in dots],
                _on_finish=lambda scene: self.add(*dots)
            )

class ReusableDemo(Scene):
    def construct(self):

        NUM_DOTS = 5

        circle = CircleWithDots()

        self.play(Create(circle))
        self.play(circle.add_dots(NUM_DOTS), run_time=1)
        self.wait(0.3)
        self.play(circle.animate.shift(DOWN))
        self.wait()





class Demo(Scene):
    def construct(self):

        NUM_DOTS = 5

        # version 1 - creates correctly, but doesn't move as a group
        circle_1 = Circle()
        group_1 = VGroup(circle_1).shift(LEFT*3)
        dots_1 = [Dot(circle_1.point_from_proportion(step/NUM_DOTS))
                  for step in range(NUM_DOTS)]

        # version 2 - groups correctly, but creation is broken
        circle_2 = Circle()
        group_2 = VGroup(circle_2)
        dots_2 = [Dot(circle_2.point_from_proportion(step/NUM_DOTS))
                  for step in range(NUM_DOTS)]

        # version 3 - create and modify working, but clunky to try and extract a reusable mobject here...
        circle_3 = Circle()
        group_3 = VGroup(circle_3).shift(RIGHT*3)
        dots_3 = [Dot(circle_3.point_from_proportion(step/NUM_DOTS))
                  for step in range(NUM_DOTS)]

        self.play(Create(group_1), Create(group_2), Create(group_3))
        self.wait()

        # attempt #1
        self.play(
            Succession(
                *[Create(dot) for dot in dots_1]
            ), run_time=1
        )
        self.wait(0.3)
        self.play(group_1.animate.shift(DOWN))
        self.wait()

        # attempt #2
        group_2.add(*dots_2)
        self.play(
            Succession(
                *[Create(dot) for dot in dots_2]
            ), run_time=1
        )
        self.wait(0.3)
        self.play(group_2.animate.shift(DOWN))
        self.wait()

        # attempt #3
        self.play(
            Succession(
                *[Create(dot) for dot in dots_3]
            ), run_time=1
        )
        group_3.add(*dots_3)
        self.wait(0.3)
        self.play(group_3.animate.shift(DOWN))
        self.wait()


class Playground(Scene):
    def construct(self):

        # version 1 - creates correctly, but doesn't move as a group
        notes_1 = VDict()
        bg_circle_1 = Circle().shift(LEFT * 3).rotate(90 * PI / 180).flip()
        group_1 = VGroup(bg_circle_1, notes_1)

        # version 2 - groups correctly, but creation is broken
        notes_2 = VDict()
        bg_circle_2 = Circle().rotate(90 * PI / 180).flip()
        group_2 = VGroup(bg_circle_2, notes_2)

        # version 3 - create and modify working, but is this really how it's supposed to be done?
        notes_3 = VDict()
        bg_circle_3 = Circle().shift(RIGHT * 3).rotate(90 * PI / 180).flip()
        group_3 = VGroup(bg_circle_3, notes_3)
        
        def make_dot_at_step(step: float, circle: Circle) -> Dot:
            "Given a circle and a step in [0,8), create a dot at that step"
            location = circle.point_from_proportion((step) / 8)
            note = Dot().move_to(location)
            return note

        def add_note(step: float, circle: Circle, notes_group: VDict):
            """Given a circle, a step in [0,8), and a VDict,
            create a dot at that step, and add it to the VDict."""
            note = notes_group[step] = make_dot_at_step(step=step, circle=circle)
            return note
        
        note_steps = [0, 2, 3, 5, 6]
        
        self.play(Create(group_1), Create(group_2), Create(group_3))
        self.wait()
        
        # attempt #1
        self.play(
            Succession(
                *[Create(make_dot_at_step(step, bg_circle_1))
                    for step in note_steps]
            ), run_time=1
        )
        self.wait(0.3)
        self.play(
            group_1.animate.shift(DOWN)
        )
        self.wait()

        # attempt #2
        self.play(
            Succession(
                *[Create(add_note(step, bg_circle_2, notes_2))
                    for step in note_steps
                ]
            ), run_time=1
        )
        self.wait(0.3)
        self.play(
            group_2.animate.shift(DOWN)
        )
        self.wait()
        
        # attempt #3
        notes = {step: make_dot_at_step(step, bg_circle_3) for step in note_steps}
        self.play(
            Succession(
                *[Create(note) for note in notes.values()]
            ), run_time=1
        )
        for step, note in notes.items():
            notes_3[step] = note
        self.wait(0.3)
        self.play(
            group_3.animate.shift(DOWN)
        )
        self.wait()

        # # def add_notes(self, notes: list[int], run_time: float=1) -> Animation:
        # #     step_run_time = run_time / self.prop_divisions
        # #     print(f"{step_run_time=}")
        # #     animations = []
        # #     for step in range(1, self.prop_divisions+1):
        # #         if step in notes:
        # #             animations.append(self.add_note(step).set_run_time(step_run_time))
        # #         else:
        # #             animations.append(Wait(run_time=step_run_time))
        # #     return Succession(*animations)

        # self.wait()
        # # self.play()
        # self.wait(0.2)
