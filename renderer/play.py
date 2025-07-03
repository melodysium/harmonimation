from manim import *
from manim.typing import *

config.disable_caching = True

from utils import point_at_angle, Anchor


class CreateCircle(Scene):
    def construct(self):
        circle = Circle(stroke_width=0)
        circle.set_fill(PINK, opacity=0.5)
        self.play(Create(circle))
        self.play(circle.animate.set_fill(RED))


class CreateSquare(Scene):
    def construct(self):
        square = Square(
            side_length=2, fill_color=GRAY, fill_opacity=1, stroke_opacity=0
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

        lambda contact: contact["asdf"]["qwer"]


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

        group.add(CircledNumber(1))
        group.add(CircledNumber(4))
        group.add(CircledNumber(2))
        group.add(CircledNumber(8))
        group.add(CircledNumber(5))
        group.add(CircledNumber(7))

        group.arrange(RIGHT)

        self.play(Create(group))
        self.wait()
        self.play(group.animate.sort(submob_func=lambda x: x.number), path_arc=2)
        self.wait()


class SortModified(Scene):
    def construct(self):
        group = VGroup()

        arr = [1, 4, 2, 8, 5, 7]
        group = VGroup(*[CircledNumber(n) for n in arr])
        group.arrange(RIGHT)

        self.play(DrawBorderThenFill(group))
        self.wait()
        group.sort(submob_func=lambda x: x.number)
        self.play(group.animate.arrange(RIGHT), path_arc=2)
        self.wait()


class CircledNumber(VGroup):
    def __init__(self, number, **kwargs):
        super().__init__(**kwargs)
        self.number = number

        self.circle = Circle()
        self.add(self.circle)

        self.text = Text(str(self.number)).move_to(self.circle.get_center())
        self.add(self.text)


# ----------end copied code


class CircleWithDots(VGroup):

    circle: Circle

    def __init__(self, **kwargs):
        self.circle = Circle()
        super().__init__(self.circle, **kwargs)

    def add_dots(self, num_dots: int) -> Animation:
        dots = [
            Dot(self.circle.point_from_proportion(step / num_dots))
            for step in range(num_dots)
        ]
        return Succession(
            *[Create(dot) for dot in dots], _on_finish=lambda scene: self.add(*dots)
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
        group_1 = VGroup(circle_1).shift(LEFT * 3)
        dots_1 = [
            Dot(circle_1.point_from_proportion(step / NUM_DOTS))
            for step in range(NUM_DOTS)
        ]

        # version 2 - groups correctly, but creation is broken
        circle_2 = Circle()
        group_2 = VGroup(circle_2)
        dots_2 = [
            Dot(circle_2.point_from_proportion(step / NUM_DOTS))
            for step in range(NUM_DOTS)
        ]

        # version 3 - create and modify working, but clunky to try and extract a reusable mobject here...
        circle_3 = Circle()
        group_3 = VGroup(circle_3).shift(RIGHT * 3)
        dots_3 = [
            Dot(circle_3.point_from_proportion(step / NUM_DOTS))
            for step in range(NUM_DOTS)
        ]

        self.play(Create(group_1), Create(group_2), Create(group_3))
        self.wait()

        # attempt #1
        self.play(Succession(*[Create(dot) for dot in dots_1]), run_time=1)
        self.wait(0.3)
        self.play(group_1.animate.shift(DOWN))
        self.wait()

        # attempt #2
        group_2.add(*dots_2)
        self.wait(0.3)
        self.play(Succession(*[Create(dot) for dot in dots_2]), run_time=1)
        self.wait(0.3)
        self.play(group_2.animate.shift(DOWN))
        self.wait()

        # attempt #3
        self.play(Succession(*[Create(dot) for dot in dots_3]), run_time=1)
        group_3.add(*dots_3)
        self.wait(0.3)
        self.play(group_3.animate.shift(DOWN))
        self.wait()


# NOTE: this is basically the same as the above scene, just placing the dots at weird spots
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
                *[Create(make_dot_at_step(step, bg_circle_1)) for step in note_steps]
            ),
            run_time=1,
        )
        self.wait(0.3)
        self.play(group_1.animate.shift(DOWN))
        self.wait()

        # attempt #2
        self.play(
            Succession(
                *[Create(add_note(step, bg_circle_2, notes_2)) for step in note_steps]
            ),
            run_time=1,
        )
        self.wait(0.3)
        self.play(group_2.animate.shift(DOWN))
        self.wait()

        # attempt #3
        notes = {step: make_dot_at_step(step, bg_circle_3) for step in note_steps}
        self.play(Succession(*[Create(note) for note in notes.values()]), run_time=1)
        for step, note in notes.items():
            notes_3[step] = note
        self.wait(0.3)
        self.play(group_3.animate.shift(DOWN))
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
        self.add(
            Text(text=text, font_size=text_font_size).next_to(
                self, DOWN, buff=SMALL_BUFF
            )
        )


class ChangeText(Scene):
    def construct(self):
        text = Text("Text").move_to(LEFT * 2)
        tex = Tex("Tex").move_to(RIGHT * 2)
        newText = Text("New Text").move_to(LEFT * 2)
        newTex = Tex("New Tex").move_to(RIGHT * 2)
        nothingText = Text("").move_to(LEFT * 2)
        nothingTex = Tex("").move_to(RIGHT * 2)

        self.play(Create(text), Create(tex))
        self.wait(1)

        self.play(Transform(text, newText), Transform(tex, newTex), run_time=0.000001)
        self.wait(1)

        self.play(Transform(text, nothingText), Transform(tex, nothingTex))
        self.wait(1)


class TextAlignment(Scene):
    def construct(self):
        label = Text("Leters: ")
        value = Text("a PTWY").next_to(label, RIGHT)
        underline = Line(value.get_corner(DOWN + LEFT), value.get_corner(DOWN + RIGHT))
        self.add(label, value, underline)
        self.wait(1)

        new_value = Text("a gpqy").next_to(label, RIGHT)
        self.play(Transform(value, new_value), run_time=1)
        self.wait(1)


class ScreenMap(Scene):
    def construct(self):
        # make axes, with units matching screen size
        ax = Axes(
            x_length=14,
            y_length=8,
            axis_config={
                "tip_shape": StealthTip,
            },
        ).add_coordinates()
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
        graydient = color_gradient(
            [BLUE, BLUE.to_rgba_with_alpha(0.2)], length_of_output=20
        )
        # NOTE: opacity must be set separately from color
        line = (
            Line(
                start=LEFT * 3,
                end=RIGHT * 3,
                stroke_width=10,
                # stroke_color=[RED, BLUE.to_rgba_with_alpha(0.01)],
                # stroke_opacity=[1, 0],
            )
            .set_color(color=[RED, BLUE.to_rgba_with_alpha(0.2)])
            .set_opacity([1, 0])
        )
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


# from Reddit:
# https://www.reddit.com/r/manim/comments/16z0j9n/clarification_on_how_gradient_works/
class gradLines(Scene):
    def construct(self):
        for i in range(10):
            self.add(
                Line(
                    start=ORIGIN,
                    end=[3 * np.cos(2 * PI * i / 10), 3 * np.sin(2 * PI * i / 10), 0],
                    stroke_color=[PURE_GREEN, WHITE],
                    stroke_width=15,
                ).shift(3.5 * LEFT),
                Line(
                    start=ORIGIN,
                    end=[3 * np.cos(2 * PI * i / 10), 3 * np.sin(2 * PI * i / 10), 0],
                    stroke_color=[PURE_GREEN, WHITE],
                    stroke_width=15,
                )
                .set_sheen_direction(
                    [3 * np.cos(2 * PI * i / 10), 3 * np.sin(2 * PI * i / 10), 0]
                )
                .shift(3.5 * RIGHT),
            )


class testTextProperties(Scene):
    def construct(self):
        color_text = Text(
            "Text color",
            font_size=80,
            stroke_width=3,
            stroke_color=BLUE,
            fill_color=GREEN,
            # color=RED,
            weight=BOLD,
        ).shift(UP + LEFT)
        color_tex = Tex(
            r"Tex \textbf{col}or",
            font_size=80
            * 1.5,  # weirdly needs 1.5x scaling to look mostly the same size
            stroke_width=3,
            stroke_color=BLUE,  # somehow takes priority over color if fill_color is unset
            fill_color=GREEN,
            # color=RED,
            # weight=BOLD,  # doesn't work on Tex, causes crash
        ).shift(DOWN + LEFT)
        self.play(
            Create(e)
            for e in (
                color_text,
                color_tex,
            )
        )
        self.wait(2)


class testTexBoldSyllableChange(Scene):
    def construct(self):
        myTemplate = TexTemplate()
        myTemplate.add_to_preamble(
            r"""
        \usepackage{xcolor}
        """
        )
        lyrics = ["O", "ya", "su", "mi"]
        syllable_stressed_lyrics = [
            [
                (
                    r"{\color{white}" + l + r"}"
                    if l is bolded_l
                    else r"{\color{gray}" + l + r"}"
                )
                for l in lyrics
            ]
            for bolded_l in lyrics
        ]

        for ssl in syllable_stressed_lyrics:
            print(f"  {ssl}")
        mTexs = [
            Tex(
                "-".join(syl_lyric),
                tex_template=myTemplate,
                color=WHITE,
                # font_size=30,
            ).shift(UP * (3 - (2 * idx)) + LEFT * 2)
            for idx, syl_lyric in enumerate(syllable_stressed_lyrics)
        ]
        print(mTexs)
        self.play(Create(m) for m in mTexs)
        self.wait(1)

        # uncolored_mTex = Tex(
        #     "-".join(syl_lyric for syl_lyric in lyrics),
        #     tex_template=myTemplate,
        #     color=WHITE,
        #     # font_size=30,
        # ).shift(RIGHT * 2)
        # anim_mTexs = [
        #     Tex(
        #         "-".join(syl_lyric),
        #         tex_template=myTemplate,
        #         color=WHITE,
        #         # font_size=30,
        #     ).shift(RIGHT * 2)
        #     for syl_lyric in syllable_stressed_lyrics
        # ]
        # self.play(Create(uncolored_mTex))
        # print(f"{0}, {uncolored_mTex.tex_string}")
        # for idx, anim_mTex in enumerate(anim_mTexs):
        #     print(f"{idx}, {anim_mTex.tex_string}")
        #     self.play(Transform(uncolored_mTex, anim_mTex))
        # self.wait(2)

        # # maybe it looks better if each syllable is its own Tex object?

        syllable_stressed_lyrics = [
            [
                (
                    r"{\textbf{}" + l + r"}"
                    if l is bolded_l
                    else r"{\color{gray}" + l + r"}"
                )
                for l in lyrics
            ]
            for bolded_l in lyrics
        ]
        ssl_with_dashes = [
            [f"{l}-" if idx + 1 < len(ssl) else l for idx, l in enumerate(ssl)]
            for ssl in syllable_stressed_lyrics
        ]
        anim_mTexs: list[VGroup] = []
        for ssl in ssl_with_dashes:
            g = VGroup()
            start = Tex(ssl[0])
            g.add(start)
            prev = start
            for syl in ssl:
                new_tex = Tex(syl).next_to(prev, RIGHT)
                prev = new_tex
                g.add(new_tex)
            g.move_to(RIGHT * 2)
            anim_mTexs.append(g)
        self.play(Create(anim_mTexs[0]))
        # print(f"{0}, {anim_mTexs[0]}")
        for idx, anim_mTex in enumerate(anim_mTexs):
            if idx == 0:
                continue
            # print(f"{idx}, {anim_mTex.tex_string}")
            self.play(ReplacementTransform(anim_mTexs[idx - 1], anim_mTex))
        self.wait(2)
        # # nonononononononononononononono they have different vertical alignments :(


class testTexColor(Scene):
    def construct(self):
        myTemplate = TexTemplate()
        myTemplate.add_to_preamble(
            r"""
        \usepackage{xcolor}
        """
        )
        t = Tex(
            r"Default text. {\color{gray}Gray text.} Default text. {\color{lightgray}Black text.}",
            color=WHITE,
            tex_template=myTemplate,
        )
        self.play(Create(t))
        self.wait(2)


class testAnimationGroupWithDifferentRunTimes(Scene):
    def construct(self):
        circle = Circle().shift(UP)
        square = Square().shift(DOWN)
        self.play(
            AnimationGroup(Create(circle, run_time=1), Create(square, run_time=2))
        )
        self.wait(1)
        self.play(
            AnimationGroup(
                circle.animate(run_time=2).shift(RIGHT),
                square.animate(run_time=1).shift(RIGHT),
            )
        )


class MoveToAngleOnCircle(Animation):

    circle: Circle
    target: Mobject
    start_angle: float
    final_angle: float
    angle_diff: float

    def __init__(
        self,
        circle: Circle,
        target: Mobject,
        start_angle: float,
        final_angle: float,
        **kwargs,
    ):
        self.circle = circle
        self.target = target
        self.start_angle = start_angle
        self.final_angle = final_angle
        self.angle_diff = final_angle - start_angle  # simple version for now
        super().__init__(target, **kwargs)

    def interpolate_mobject(self, alpha):
        self.target.move_to(
            self.circle.point_at_angle(self.start_angle + self.angle_diff * alpha)
        )


class testMoveTextAlongCircleWhileChangingColor(Scene):

    def construct(self):
        circle = Circle(radius=3)
        text = Text("Hi!").move_to(circle.point_at_angle(PI))
        self.play(Create(circle), Create(text))
        self.wait(1)

        # TODO: why does this get invoked about 3x more than it should?
        move_along_arc_progress = 0

        def move_along_arc(mobject: Text, dt: float):
            nonlocal move_along_arc_progress
            move_along_arc_progress += dt
            print(f"{dt=}, {move_along_arc_progress=}")
            pct_complete = min(move_along_arc_progress, 1)
            mobject.move_to(circle.point_at_angle(PI - PI * pct_complete))

        text.add_updater(move_along_arc)
        self.play(
            # MoveToAngleOnCircle(circle, text, PI, 0),
            # MoveAlongPath(text, Arc(radius=3, start_angle=PI, angle=-PI)),
            text.animate.set_color(BLUE),
            # Wait(),
            run_time=1,
        )
        text.remove_updater(move_along_arc)
        self.wait(1)


class AnchoredText(Text):
    anchor: Anchor

    def __init__(self, text: str, point: Point3D = ORIGIN, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.anchor = Anchor(point=point, fill_opacity=1).add_follower(self)


class testMoveTextAlongCircleWhileChangingColorFixed(Scene):

    def construct(self):
        circle = Circle(radius=3)
        # .move_to((0, 0, -1))
        texts: list[AnchoredText] = []
        rotation_group = VGroup()
        for idx, text in enumerate(("East", "North", "West", "South")):
            dir_text = AnchoredText(
                text, point=point_at_angle(circle, angle=TAU * (idx / 4))
            )
            texts.append(dir_text)
            rotation_group.add(dir_text.anchor)
        # self.add(text_anchor)
        self.play(
            Create(circle),
            *(Create(t) for t in texts),
        )
        self.add(rotation_group)
        # self.wait(1)

        # self.play(
        #     Rotate(
        #         rotation_group,
        #         angle=-PI,
        #         about_point=circle.get_center(),
        #     ),
        #     *(t.animate.set_color(BLUE) for t in texts),
        #     run_time=1,
        # )
        # self.wait(1)

        self.play(
            Succession(
                AnimationGroup(
                    *(t.animate.set_color(GREEN) for t in texts),
                ),
            ),
            Succession(
                AnimationGroup(
                    Rotate(
                        rotation_group,
                        angle=-PI,
                        about_point=circle.get_center(),
                    ),
                ),
            ),
        )
        self.wait(1)


class testCirclePointAtAngle(Scene):

    def construct(self):
        # Flip circle so that it starts on LEFT, then rotate 1/4 turn clockwise
        # At the end of this, the start of the circle is at UP, and it proceeds clockwise from there
        bad_circle = (
            Circle(radius=2, stroke_color=RED)
            .flip()
            .rotate(1 / 4 * -TAU)
            .move_to(LEFT * 3)
        )
        bad_text = Text(
            "using Circle.point_at_angle()", color=RED, font_size=24
        ).next_to(bad_circle, DOWN)
        good_circle = (
            Circle(radius=2, stroke_color=GREEN)
            .flip()
            .rotate(1 / 4 * -TAU)
            .move_to(RIGHT * 3)
        )
        good_text = Text("fixed version", color=GREEN, font_size=24).next_to(
            good_circle, DOWN
        )
        self.play(
            Create(bad_circle), Create(bad_text), Create(good_circle), Create(good_text)
        )
        self.wait(1)

        def fixed_point_at_angle(circle: Circle, angle: float) -> Point3D:
            proportion = (angle) / TAU
            proportion -= np.floor(proportion)
            return circle.point_from_proportion(proportion)

        # Create 12 white dots, spaced evenly around the circle, STARTING where the circle starts.
        for i in range(12):
            # BUG: These dots start at LEFT instead of UP.
            # This is because of the logic in point_at_angle:
            # - start_angle is computed by projecting circle.points[0] onto the XY plane,
            #   then reading its angle via angle_of_vector() .. as if the circle was still in "mathematical" orientation.
            #   here, `start_angle` takes the value 1.570796..., i.e. 90° counterclockwise from mathemetical 0° rotation.
            # - proportion is then computed as (angle - start_angle) / TAU.
            #   but param `angle` is "The angle of the point along the circle in radians." Doesn't that mean "from self.points[0]"?
            #   shouldn't `angle=0` return a point at `self.points[0]`?
            #   instead proportion takes (0 - 1.570796...) / TAU = -0.75, then the cycling with `np.floor()` brings it to 0.25.
            # TODO: fix for this should be to just remove start_angle in point_at_angle(). calculate `proportion` as `angle / TAU`.
            self.add(
                Point(
                    bad_circle.point_at_angle(TAU * i / 12),
                    color=WHITE,
                    stroke_width=10,
                )
            )
            self.add(
                Point(
                    fixed_point_at_angle(good_circle, TAU * i / 12),
                    color=WHITE,
                    stroke_width=10,
                )
            )
            self.wait(0.3333333)

        self.wait(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("scene", nargs="?", default=None)
    args = parser.parse_args()
    scene_name = args.scene

    if scene_name is None:
        scene_name = input("Please enter a scene name to render: ")

    assert scene_name in globals(), f"{scene_name} is not a declared member in play.py"
    scene_cls = globals()[scene_name]
    assert issubclass(scene_cls, Scene), f"{scene_cls} is not a {Scene}"
    print(f"Attempting to render {scene_name}")
    scene_cls().render()
