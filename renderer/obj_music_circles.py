#!/usr/bin/env python3.11

# standard libs
from typing import Callable, Iterable
import logging

# 3rd party libs
from manim import *
from manim.typing import Vector3D, Point3D
from music21 import stream, note
from music21.pitch import Pitch
from more_itertools import peekable

# my files
from music.music_constants import note_for_step
from obj_music_text import NoteText
from musicxml import MusicData, MusicDataTiming
from utils import (
    TimestampedAnimationSuccession,
    point_at_angle,
    get_ionian_root,
    vector_on_unit_circle_clockwise_from_top,
    generate_group,
    pick_preferred_rotation,
)

# log setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class LabelledCircle(VGroup):

    def __init__(self, circle_color=RED, text="Circle", **kwargs):
        VGroup.__init__(self, **kwargs)
        self.circle_color = circle_color
        self.circle = Circle(color=circle_color)
        self.text = Text(text=text)
        self.add(self.circle)
        self.add(self.text)

    def create(self):
        return AnimationGroup(Create(self.circle), Create(self.text), lag_ratio=0.5)


class testLabelledCircle(Scene):
    def construct(self):
        circle = LabelledCircle()
        self.play(circle.create(), run_time=2)
        self.wait(1)


def get_line_between_two_circle_edges(c1: Circle, c2: Circle):
    direction = Line(c1.get_center(), c2.get_center()).get_unit_vector()
    c1_point = c1.get_center() + direction * c1.radius
    c2_point = c2.get_center() - direction * c2.radius
    return Line(c1_point, c2_point)


# TODO: add non-root "highlights" around other notes being played
BASE_PITCH_LABEL_FONT_SIZE = 16
BASE_PITCH_CIRCLE_RADIUS = 0.2
DEFAULT_ROTATE_TRANSITION_TIME = 0.3


class Circle12NotesBase(VGroup):

    # mobjects
    mob_circle_background: Circle
    mob_pitches: VDict  # VDict[int, NoteText]
    mob_select_circles: VDict  # VDict[int, Circle]

    # properties
    circle_color: ParsableManimColor
    radius: float
    start_pitch_idx: int = 0  # TODO: make this configurable?
    steps_per_pitch: int
    rotate_angle: float  # in unit rotations i.e. 1 = 360 deg; positive = clockwise

    def __init__(
        self,
        circle_color=GRAY,
        radius: float = 1,
        steps_per_pitch: int = 1,
        rotate_angle: float = None,
        rotate_pitch: int = None,
        **kwargs,
    ):
        VGroup.__init__(self, **kwargs)
        # save properties
        self.circle_color = circle_color
        self.radius = radius
        self.steps_per_pitch = steps_per_pitch
        assert (
            rotate_angle is None or rotate_pitch is None
        ), f"cannot set both rotate_angle and rotate_step for {Circle12NotesBase.__name__}"
        self.rotate_angle = (
            -self.compute_angle_for_pitch(rotate_pitch, 0)
            if rotate_pitch
            else rotate_angle if rotate_angle else 0
        )
        # print(f"Circle12NotesBase(): {steps_per_pitch=}, {self.rotate_angle=}")

        # add background circle
        self.mob_circle_background = (
            Circle(
                color=circle_color,
                radius=radius,
                stroke_opacity=0.3,
                stroke_width=8,
            )  # starts with "math" orientation - circle starts at RIGHT and proceeds counter-clockwise
            .flip()  # flip vertically - now circle starts LEFT and goes clockwise
            .rotate(1 / 4 * -TAU)  # rotate 1/4 to start UP
            .rotate(self.rotate_angle * -TAU)
        )
        self.add(self.mob_circle_background)
        # set up pitches
        self.mob_pitches = VDict()
        self.add(self.mob_pitches)
        self.mob_select_circles = VDict()
        self.add(self.mob_select_circles)
        # create 12 individual pitches and small highlight circles
        for pitch_idx, pitch_pos in self._list_positions():
            pitch = note_for_step(pitch_idx)
            # create NoteText and circle in correct position
            pitch_label = NoteText(
                pitch, font_size=BASE_PITCH_LABEL_FONT_SIZE * radius
            ).shift(pitch_pos)
            pitch_circle = Circle(
                color=WHITE, radius=BASE_PITCH_CIRCLE_RADIUS * radius, stroke_opacity=0
            ).move_to(pitch_label)
            # save mobjects, add pitch text
            self.mob_pitches[pitch.scale_step] = pitch_label
            self.mob_select_circles[pitch.scale_step] = pitch_circle

    def _list_steps(self) -> Iterable[tuple[int, int]]:  # (pitch, step)
        for step_idx, pitch_idx in enumerate(
            generate_group(
                start=self.start_pitch_idx,
                step=self.steps_per_pitch,
                size=12,
            )
        ):
            yield (step_idx, pitch_idx)

    def _list_positions(self) -> Iterable[tuple[int, Vector3D]]:
        for step_idx, pitch_idx in self._list_steps():
            print(
                f"_list_positions(): {step_idx=}, {pitch_idx=}, pos={point_at_angle(self.mob_circle_background, TAU * step_idx / 12)}"
            )
            # calculate position
            yield (
                pitch_idx,
                point_at_angle(self.mob_circle_background, TAU * step_idx / 12),
            )

    # TODO: fix bug where self isn't created, but all its submobjects are
    def create(self) -> Animation:
        return AnimationGroup(
            Create(self.mob_circle_background, rate_func=rate_functions.ease_in_sine),
            AnimationGroup(
                Create(self.mob_pitches),
                Create(self.mob_select_circles),
            ),
            lag_ratio=0.18,
        )

    def get_pitch_text(self, pitch_idx: int) -> NoteText:
        """Gets the pitch text for a given pitch_idx"""
        return self.mob_pitches[pitch_idx]

    def get_pitch_circle(self, pitch_idx: int) -> Circle:
        """Gets the highlight circle around the pitch text for a given pitch_idx"""
        return self.mob_select_circles[pitch_idx]

    def get_center(self) -> Point3D:
        return self.mob_circle_background.get_center()

    def compute_angle_for_pitch(
        self, pitch_idx: int, rotate_angle: float = None
    ) -> float:
        """Compute the angle (0-1) for the given step, including any current rotation.

        If you want to compute without any current rotation, set rotate_angle=0"""

        # number of pitches past the start pitch.
        # if start pitch is D, Eb is 1 pitch past
        pitches_past_start = (pitch_idx - self.start_pitch_idx) % 12
        # number of steps past the top of the circle.
        # if start pitch is D, and steps_per_pitch is 7, Eb is 7 steps past
        steps_past_top = (pitches_past_start * self.steps_per_pitch) % 12
        # use provided rotate_angle if any, otherwise take from self
        rotate_angle_to_use = (
            rotate_angle if rotate_angle is not None else self.rotate_angle
        )
        # compute final angle
        final_angle = steps_past_top / 12 + rotate_angle_to_use
        # print(
        #     f"compute_angle_for_pitch({pitch_idx=}, {rotate_angle=}) ({self.steps_per_pitch=}). {pitches_past_start=}, {steps_past_top=}, {rotate_angle_to_use=}, {final_angle=}"
        # )
        return final_angle

    def rotate_to(self, angle: float) -> float:
        """Rotate the music circle to the given angle (unit=rotations).

        0 = start_pitch at top.
        Returns the actual rotation as the difference between new and old angle."""

        rotate_diff = angle - self.rotate_angle
        self.rotate_angle = angle

        # rotate some things in-place
        self.mob_circle_background.rotate(angle=rotate_diff * -TAU)

        # for others, calculate new positions and move to there
        for pitch_idx, pitch_pos in self._list_positions():
            self.get_pitch_text(pitch_idx).move_to(pitch_pos)
            self.mob_select_circles[pitch_idx].move_to(pitch_pos)
        return rotate_diff

    def rotate_to_pitch(self, pitch_idx: int) -> None:
        """Rotate the music circle to have step_idx at top"""
        angle_for_pitch = -self.compute_angle_for_pitch(pitch_idx, rotate_angle=0)
        # print(f"rotate_to_pitch(), {pitch_idx=}, {angle_for_pitch=}")
        self.rotate_to(angle_for_pitch)

    def animate_rotate_to_pitch(self, pitch_idx: int, run_time: float = 1) -> Animation:
        # compute the end state
        angle_for_pitch = -self.compute_angle_for_pitch(pitch_idx, rotate_angle=0)
        # print(
        #     f"Circle12Notes({self.steps_per_pitch=}).animate_rotate_to_pitch({pitch_idx=}): {angle_for_pitch=}"
        # )
        return RotateCircle12Notes(
            self,
            angle_for_pitch,
            run_time=run_time,
        )

    def play(stream: stream.Stream, bpm: int) -> Animation:
        bps = bpm / 60

        pass  # TODO: implement


class RotateCircle12Notes(Animation):

    circle12: Circle12NotesBase
    start_angle: float = None  # lazy computed
    end_angle: float
    angle_diff: float = None  # lazy computed

    def __init__(
        self,
        circle12: Circle12NotesBase,
        end_angle: float,  # unit rotations
        run_time: float = 1,
        **kwargs,
    ):
        super().__init__(mobject=circle12, run_time=run_time, **kwargs)
        self.circle12 = circle12
        self.end_angle = end_angle
        # start_angle and angle_diff will be lazy computed

    def interpolate_mobject(self, alpha: float):
        # lazy compute the rotation to perform
        if self.angle_diff is None:
            self.start_angle = self.circle12.rotate_angle
            self.angle_diff = pick_preferred_rotation(self.start_angle, self.end_angle)
            # print(
            #     f"RotateCircle12Notes: Circle12Notes({self.circle12.steps_per_pitch=}), {self.start_angle=}, {self.end_angle=}, {self.angle_diff=}, {self.rate_func}"
            # )

        old_rotate_angle = self.circle12.rotate_angle
        self.circle12.rotate_to(
            self.start_angle + self.angle_diff * self.rate_func(alpha)
        )
        # print(
        #     f"RotateCircle12Notes.interpolate_mobject({alpha=}): {old_rotate_angle=}, {self.circle12.rotate_angle}"
        # )


class Circle12NotesSequenceConnectors(Circle12NotesBase):

    # mobjects
    mob_select_connectors: VGroup  # VGroup[Line]
    hack_select_connectors: list[Line]

    # properties
    max_selected_steps: int
    calculate_circle_opacity: Callable[[int, int], float]

    def calculate_circle_opacity_default(
        select_idx: int, max_selected_steps: int
    ) -> float:
        pct = select_idx / max_selected_steps
        return (1 - pct) ** 1.5

    # implementation details
    _selected_pitches: list[int]

    def __init__(
        self,
        circle_color=GRAY,
        radius: float = 1,
        steps_per_pitch: int = 1,
        rotate_angle: float = None,
        rotate_pitch: int = None,
        max_selected_steps: int = 3,
        select_circle_opacity=calculate_circle_opacity_default,
        **kwargs,
    ):
        Circle12NotesBase.__init__(
            self,
            circle_color,
            radius,
            steps_per_pitch,
            rotate_angle,
            rotate_pitch,
            **kwargs,
        )
        # initialize fields
        self._selected_pitches = []
        self.hack_select_connectors = (
            []
        )  # TODO: figure out a better hack. maybe subclass VGroup?
        self.mob_select_connectors = VGroup()
        self.add(self.mob_select_connectors)
        # save properties
        self.max_selected_steps = max_selected_steps
        self.calculate_circle_opacity = select_circle_opacity

    # override from parent class
    def create(self) -> Animation:
        return AnimationGroup(
            Create(self.mob_circle_background, rate_func=rate_functions.ease_in_sine),
            AnimationGroup(
                Create(self.mob_pitches),
                Create(self.mob_select_circles),
                Create(self.mob_select_connectors),
            ),
            lag_ratio=0.18,
        )

    def select_pitch(self, pitch_idx: int):
        logger.debug(
            f"  invoke select_pitch({pitch_idx}); {self._selected_pitches=}, {self.max_selected_steps}, {self.hack_select_connectors}: ",
            end="",
        )

        # if already selected, ignore
        if self._selected_pitches and pitch_idx is self._selected_pitches[0]:
            logger.debug(
                f"ignoring redundant select_pitch({pitch_idx}); already selected"
            )
            return

        # mark this pitch as selected
        self._selected_pitches.insert(0, pitch_idx)

        # if there is a previous selected pitch, add a connector
        if len(self._selected_pitches) >= 2:
            # TODO: maybe check if this connector already exists?
            # get circle centers
            new_select_circle = self.mob_select_circles[self._selected_pitches[0]]
            prev_select_circle = self.mob_select_circles[self._selected_pitches[1]]
            # create connector line
            mob_connector = get_line_between_two_circle_edges(
                prev_select_circle, new_select_circle
            )
            # mob_connector = get_line_between_two_circle_edges(*(self.mob_select_circles[self._selected_steps[idx]] for idx in range(2)))
            # add connector to shape
            self.hack_select_connectors.insert(0, mob_connector)
            self.mob_select_connectors.add(mob_connector)
            # self.add(mob_connector) # TODO: had this, commented it out to fix a bug. can probably remove?

        # if we're over our limit, un-select an old step and make it invisible
        if len(self._selected_pitches) > self.max_selected_steps:
            # remove the circle
            old_step: int = self._selected_pitches.pop()
            self.get_pitch_circle(pitch_idx=old_step).set_stroke(opacity=0)
            # remove the oldest connector
            old_select_connector = self.hack_select_connectors.pop()
            self.mob_select_connectors.remove(old_select_connector)

        # update opacities for all remaining select circles and connectors
        # reversed() starts at the oldest (dimmest) circle, so that if it's also selected in a newer step, that one is used instead
        for select_idx, select_step in reversed(
            list(enumerate(self._selected_pitches))
        ):
            new_opacity = self.calculate_circle_opacity(
                select_idx, self.max_selected_steps
            )
            # TODO: why does this only work with set_stroke(opacity=x), and not setting stroke_opacity directly?
            # self.get_pitch_circle(pitch_idx=select_step).stroke_opacity = new_opacity
            self.get_pitch_circle(pitch_idx=select_step).set_stroke(opacity=new_opacity)
            print(
                f"select_pitch(): {select_idx=}, {select_step=}, {new_opacity=}, {self.get_pitch_circle(pitch_idx=select_step)=}, {self.get_pitch_circle(pitch_idx=select_step).stroke_opacity=}"
            )
            # dont update a connector that doesn't exist
            if select_idx != len(self._selected_pitches) - 1:
                mob_select_connector = self.hack_select_connectors[select_idx]
                mob_select_connector.set_stroke(opacity=new_opacity)
        return self

    def rotate_to(self, angle: float) -> None:
        rotate_diff = super().rotate_to(angle)
        # print(
        #     f"Circle12NoteSequenceConnectors({self.steps_per_pitch=}).rotate_to({angle=}): {rotate_diff=}"
        # )
        for mob_connector in self.mob_select_connectors:
            mob_connector.rotate(
                angle=rotate_diff * -TAU, about_point=self.get_center()
            )

    def play(self, music_data: MusicData) -> Animation:
        return PlayCircle12Notes(
            circle12=self,
            music_data=music_data,
            transition_time=DEFAULT_ROTATE_TRANSITION_TIME,
        )


class PlayCircle12Notes(AnimationGroup):

    def __init__(
        self,
        circle12: Circle12NotesBase,
        music_data: MusicData,
        transition_time: float,
        **kwargs,
    ):
        anims: list[Animation] = []

        # only add rotations if there are key changes
        if len(music_data.keys) > 1:
            anims.append(
                PlayCircle12NotesKeyChanges(
                    circle12=circle12,
                    music_data=music_data,
                    transition_time=transition_time,
                    **kwargs,
                )
            )
        # only add chord animations if there are any chords in the piece
        if len(music_data.chord_roots()) > 0:
            anims.append(
                PlayCircle12NotesSelectChordRoots(
                    circle12=circle12,
                    music_data=music_data,
                    **kwargs,
                )
            )
        super().__init__(anims, **kwargs)


class PlayCircle12NotesKeyChanges(TimestampedAnimationSuccession):

    def __init__(
        self,
        circle12: Circle12NotesBase,
        music_data: MusicData,
        transition_time: float,
        **kwargs,
    ):
        # build a sequence of animations to play - waits followed by rotations
        anims: list[tuple[float, Animation]] = []
        previous_pitch_class: int = get_ionian_root(music_data.keys[0].elem).pitchClass

        for key_info in music_data.keys[1:]:
            # figure out which pitch to use
            # TODO: whether to use tonic or ionian root at top should be a config option
            pitch = get_ionian_root(key_info.elem)
            assert pitch is not None
            if pitch.pitchClass == previous_pitch_class:
                continue  # no need to rotate to same pitch

            # create animation for this key change
            anim = circle12.animate_rotate_to_pitch(pitch.pitchClass)
            anims.append((key_info.time, anim))

            # done processing this key change
            previous_pitch_class = pitch.pitchClass

        super().__init__(anims, transition_time, **kwargs)


class PlayCircle12NotesSelectChordRoots(Animation):

    # TODO: rework into a play() method on Circle12Notes
    # can still be a class within Circle12Notes,
    # but that play() method should be a common interface

    # beats per second
    total_time: float
    circle12: Circle12NotesSequenceConnectors
    pitches_gen: peekable  # Iterator[tuple[OffsetQL, Pitch]]
    last_pitch: Pitch = None

    def __init__(
        self,
        circle12: Circle12NotesSequenceConnectors,
        music_data: MusicData,
        **kwargs,
    ):
        pitches = music_data.chord_roots()
        self.total_time = pitches[-1].time + 1
        super().__init__(circle12, run_time=self.total_time, **kwargs)
        self.circle12 = circle12
        self.pitches_gen = peekable(pitches)

    def interpolate_mobject(self, alpha: float):
        current_time = alpha * self.total_time
        try:
            while self.pitches_gen.peek().time <= current_time:
                pitch_info: MusicDataTiming[Pitch] = next(self.pitches_gen)
                if (
                    self.last_pitch is not None
                    and pitch_info.elem.pitchClass == self.last_pitch.pitchClass
                ):
                    continue  # no need to highlight same pitch again
                self.circle12.select_pitch(pitch_info.elem.pitchClass)
                self.last_pitch = pitch_info.elem
        except StopIteration:
            return


# class AddNoteCircle(Animation):
#   def __init__(self, circle_12_notes: Circle12Notes, )


class test(Scene):
    def construct(self):
        self.wait(0.2)

        circle_chromatic = Circle12NotesSequenceConnectors(
            radius=1.5,
            rotate_pitch=5,
            max_selected_steps=5,
        ).shift(2 * LEFT)
        circle_fifths = Circle12NotesSequenceConnectors(
            radius=1.5,
            steps_per_pitch=7,
            rotate_pitch=5,
            max_selected_steps=5,
        ).shift(2 * RIGHT)
        self.play(circle_chromatic.create(), circle_fifths.create(), run_time=2)
        self.wait(1)

        # # test selecting pitches
        # step_count = 12 * 1 + 1
        # step_base = 12
        # step_delay_start = 0.1
        # for step in range(step_count):
        #     circle_chromatic.select_pitch(step % 12)
        #     circle_fifths.select_pitch(step % 12)
        #     self.wait(step_delay_start * (step_base / (step_base + step)))
        # self.wait(1)

        # test rotations
        def rotate_to_pitch_idx(pitch_idx: int):
            # print(f"rotating both circles to step {pitch_idx} on top")
            self.play(
                AnimationGroup(
                    circle_chromatic.animate_rotate_to_pitch(pitch_idx, run_time=0.5),
                    circle_fifths.animate_rotate_to_pitch(pitch_idx, run_time=0.5),
                )
            )
            circle_chromatic.select_pitch(pitch_idx)
            circle_fifths.select_pitch(pitch_idx)

        for i in range(1, 13):
            rotate_to_pitch_idx(-(2 * i + 5) % 12)
            self.wait(0.5)


class testPlay(Scene):
    def construct(self):
        self.wait(0.2)
        circle_chromatic = Circle12NotesSequenceConnectors(radius=1.5).shift(2 * LEFT)
        circle_fifths = Circle12NotesSequenceConnectors(
            radius=1.5, steps_per_pitch=7
        ).shift(2 * RIGHT)
        self.play(circle_chromatic.create(), circle_fifths.create(), run_time=2)
        self.wait(1)

        # duration.Duration()

        class StubMusicData:
            def __init__(self, pitches):
                self.pitches = pitches

            def chord_roots(self):
                return self.pitches

        melody = StubMusicData(
            [
                MusicDataTiming(note.Note("C", quarterLength=2), 1, 1),
                MusicDataTiming(note.Note("F", quarterLength=2), 2, 2),
                MusicDataTiming(note.Note("B-", quarterLength=2), 3, 3),
                MusicDataTiming(note.Note("E-", quarterLength=2), 4, 4),
                MusicDataTiming(note.Note("C", quarterLength=2), 5, 5),
                MusicDataTiming(note.Note("F", quarterLength=2), 6, 6),
                MusicDataTiming(note.Note("G", quarterLength=2.75), 7, 7),
                MusicDataTiming(note.Note("C", quarterLength=1.25), 8, 8),
            ]
        )

        play_circle_chromatic = PlayCircle12Notes(
            music_data=melody, circle12=circle_chromatic
        )
        play_circle_fifths = PlayCircle12Notes(
            music_data=melody, circle12=circle_fifths
        )
        self.play(
            AnimationGroup(
                play_circle_chromatic,
                play_circle_fifths,
            )
        )
