from manim import *
from typing import Union


class FocusOut(Transform):
    """Expand a spotlight from a position

    Parameters
    ----------
    focus_point
        The point at which to expand the spotlight. If it is a :class:`.~Mobject` its center will be used.
    opacity
        The opacity of the spotlight.
    color
        The color of the spotlight.
    run_time
        The duration of the animation.
    kwargs
        Additional arguments to be passed to the :class:`~.Succession` constructor

    # Examples
    # --------
    # .. manim:: UsingFocusOn

    #     class UsingFocusOn(Scene):
    #         def construct(self):
    #             dot = Dot(color=YELLOW).shift(DOWN)
    #             self.add(Tex("Focusing on the dot below:"), dot)
    #             self.play(FocusOn(dot))
    #             self.wait()
    """

    def __init__(
        self,
        focus_point: Union[np.ndarray, Mobject],
        opacity: float = 0.2,
        color: str = GRAY,
        run_time: float = 1,
        max_radius: float = 8,
        **kwargs
    ) -> None:
        self.focus_point = focus_point
        self.color = color
        self.opacity = opacity
        self.max_radius = max_radius
        remover = True
        starting_dot = Dot(radius=0, stroke_width=0).move_to(focus_point)
        starting_dot.set_fill(color=self.color, opacity=self.opacity)
        super().__init__(starting_dot, run_time=run_time, remover=remover, **kwargs)

    def create_target(self) -> Dot:
        final_dot = Dot(
            radius=self.max_radius,
            stroke_width=0,
            fill_color=self.color,
            fill_opacity=0,
        )
        final_dot.add_updater(lambda d: d.move_to(self.focus_point))
        return final_dot


class RippleOut(Transform):
    def __init__(
        self,
        focus_point: Union[np.ndarray, Mobject],
        opacity: float = 1,
        color: str = WHITE,
        stroke_width: float = 2,
        run_time: float = 1,
        max_radius: float = 1,
        rate_func=rate_functions.linear,
        **kwargs
    ) -> None:
        self.focus_point = focus_point
        self.color = color
        self.stroke_width = stroke_width
        self.opacity = opacity
        self.max_radius = max_radius
        remover = True
        starting_circle = Circle(radius=0).move_to(focus_point)
        starting_circle.set_stroke(
            color=self.color, width=self.stroke_width, opacity=self.opacity
        )

        super().__init__(
            starting_circle,
            run_time=run_time,
            remover=remover,
            rate_func=rate_func,
            **kwargs
        )

    def create_target(self) -> Dot:
        final_circle = Circle(
            radius=self.max_radius,
        )
        final_circle.set_stroke(color=self.color, width=0, opacity=0)
        final_circle.add_updater(lambda d: d.move_to(self.focus_point))
        return final_circle


class FocusOutScene(Scene):
    def construct(self):
        dot = Dot().shift(UP + RIGHT)
        self.play(Create(dot))

        self.wait(0.5)
        self.play(FocusOn(dot, opacity=0.5), run_time=1)
        self.wait(0.5)
        self.play(FocusOut(dot, max_radius=1, opacity=0.5), run_time=1)
        self.wait(0.5)
        self.play(RippleOut(dot, max_radius=1, run_time=1))
