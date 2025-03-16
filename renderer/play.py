from manim import *

class CreateCircle(Scene):
  def construct(self):
    circle = Circle(stroke_width=0)
    circle.set_fill(PINK, opacity=0.5)
    self.play(Create(circle))
    self.play(circle.animate.set_fill(RED))

class CreateSquare(Scene):
  def construct(self):
    square = Square(
        side_length=2,
        fill_color=GRAY,
        fill_opacity=1,
        stroke_opacity=0
        )
    self.play(Create(square))
    self.play(square.animate.rotate(180))
    self.play(square.animate.set_fill(RED))
    self.play(FadeOut(square))

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

# https://www.reddit.com/r/manim/comments/sjaghh/i_cant_get_my_head_around_mobjectsort_and_it/
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

class UnderLabeledDot(Dot):
  def __init__(self, text="Circle", text_font_size=30, **kwargs):
    Dot.__init__(self, **kwargs)
    self.add(Text(text=text, font_size=text_font_size).next_to(self, DOWN, buff=SMALL_BUFF))

class ScreenMap(Scene):
    def construct(self):
        # make axes, with units matching screen size
        ax = Axes(
            x_length=14,
            y_length=8,
            axis_config={
                'tip_shape': StealthTip,
            }).add_coordinates()
        # the default plane corresponds to the coordinates of the scene.
        plane = NumberPlane()

        # a dot with respect to the scene
        dots = [
            UnderLabeledDot(point=(2, 2, 0), color=RED, text="(2, 2)"),
            UnderLabeledDot(point=(-1, 3, 0), color=RED, text="(-1, 3)"),
            UnderLabeledDot(point=(-1, 1, 0), color=RED, text="(-1, 1)"),
            UnderLabeledDot(point=(-5, -2, 0), color=RED, text="(-5, -2)"),
            UnderLabeledDot(point=(6, -3, 0), color=RED, text="(6, -3)"),
        ]
        
        self.add(plane, *dots, ax)


class OpacityGradient(Scene):
    def construct(self):
        print(RED.to_rgba_with_alpha(1))
        print(RED.to_rgba_with_alpha(0.2))
        graydient = color_gradient([
                BLUE,
                BLUE.to_rgba_with_alpha(0.2)],
            length_of_output=20)
        # TODO: how do I actually get the opacity to actually render?
        line = Line(
            start=LEFT*3,
            end=RIGHT*3,
            stroke_width=10,
            color=ManimColor.from_rgba((0, 1, 255,255))
            )#.set_color_by_gradient(graydient)
        print(line.stroke_width)
        self.play(Create(Circle(color=RED_E, stroke_width=10)), Create(line))

class Gradient(Scene):
    def construct(self):
       gradient_circle = Circle(fill_opacity=1).set_color([ORANGE, BLUE])
    #    gradient_circle.get_sheen_factor()
    #    gradient_circle.set_sheen()
    #    gradient_circle.set_sheen_direction()
       self.add(gradient_circle)
    #    GlowDot()
class gradLines(Scene):
    def construct(self):
        for i in range(10):
            self.add(
                Line(
                    start=ORIGIN,
                    end=[3*np.cos(2*PI*i/10),3*np.sin(2*PI*i/10),0],
                    stroke_color=[PURE_GREEN,WHITE],
                    stroke_width=15
                ).shift(3.5*LEFT),
                Line(
                    start=ORIGIN,
                    end=[3*np.cos(2*PI*i/10),3*np.sin(2*PI*i/10),0],
                    stroke_color=[PURE_GREEN,WHITE],
                    stroke_width=15
                ).set_sheen_direction([3*np.cos(2*PI*i/10),3*np.sin(2*PI*i/10),0]).shift(3.5*RIGHT)
            )