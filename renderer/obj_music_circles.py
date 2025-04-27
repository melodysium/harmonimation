#!/usr/bin/env python3.11

# standard libs
from typing import Callable, Iterable
import logging

# 3rd party libs
from manim import *
from manim.typing import Vector3D
from music21 import stream, note
from music21.note import Pitch
from more_itertools import peekable

# my files
from music.music_constants import note_for_step
from obj_music_text import NoteText
from musicxml import MusicData, MusicDataTiming
from utils import (
    vector_on_unit_circle_clockwise_from_top,
    generate_group,
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


class Circle12NotesBase(VGroup):

    # mobjects
    mob_circle_background: Circle
    mob_pitches: VDict  # VDict[int, NoteText]
    mob_select_circles: VDict  # VDict[int, Circle]

    # properties
    circle_color: str
    radius: float
    start_pitch_idx: int = 0  # TODO: make this configurable?
    steps_per_pitch: int

    def __init__(
        self,
        circle_color=GRAY,
        radius: float = 1,
        steps_per_pitch: int = 1,
        **kwargs,
    ):
        VGroup.__init__(self, **kwargs)
        # save properties
        self.circle_color = circle_color
        self.radius = radius
        self.steps_per_pitch = steps_per_pitch

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
            # calculate position
            offset = vector_on_unit_circle_clockwise_from_top(
                (step_idx / 12) + self.rotate_angle
            )
            yield (
                pitch_idx,
                self.mob_circle_background.get_center() + (offset * self.radius,),
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

    def highlight_pitch(self, pitch_idx: int, opacity: float):
        """Sets the highlight circle around the pitch text for a given step to the specified opacity."""
        pitch_circle: Circle = self.mob_select_circles[pitch_idx]
        pitch_circle.set_stroke(opacity=opacity)

    def play(stream: stream.Stream, bpm: int) -> Animation:
        bps = bpm / 60

        pass  # TODO: implement


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
        max_selected_steps: int = 3,
        select_circle_opacity=calculate_circle_opacity_default,
        **kwargs,
    ):
        Circle12NotesBase.__init__(
            self,
            circle_color,
            radius,
            steps_per_pitch,
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

    def select_step(self, step: int):
        logger.debug(
            f"  invoke select_step({step}); {self._selected_pitches=}, {self.max_selected_steps}, {self.hack_select_connectors}: ",
            end="",
        )

        # if already selected, ignore
        if self._selected_pitches and step is self._selected_pitches[0]:
            logger.debug(f"ignoring redundant select_step({step}); already selected")
            return

        # mark this pitch as selected
        self._selected_pitches.insert(0, step)

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
            self.highlight_pitch(pitch_idx=old_step, opacity=0)
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
            self.highlight_pitch(pitch_idx=select_step, opacity=new_opacity)
            # dont update a connector that doesn't exist
            if select_idx != len(self._selected_pitches) - 1:
                mob_select_connector = self.hack_select_connectors[select_idx]
                mob_select_connector.set_stroke(opacity=new_opacity)
        return self

    def play(self, music_data: MusicData) -> Animation:
        return PlayCircle12Notes(music_data, self)


class PlayCircle12Notes(Animation):

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
        music_data: MusicData,
        circle12: Circle12NotesSequenceConnectors,
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
                self.circle12.select_step(pitch_info.elem.pitchClass)
                self.last_pitch = pitch_info.elem
        except StopIteration:
            return


# class AddNoteCircle(Animation):
#   def __init__(self, circle_12_notes: Circle12Notes, )


class test(Scene):
    def construct(self):
        self.wait(0.2)
        circle_chromatic = Circle12NotesSequenceConnectors(radius=1.5).shift(2 * LEFT)
        circle_fifths = Circle12NotesSequenceConnectors(
            radius=1.5,
            steps_per_pitch=7,
        ).shift(2 * RIGHT)
        self.play(circle_chromatic.create(), circle_fifths.create(), run_time=2)
        self.wait(1)
        step_count = 12 * 1 + 1
        step_base = 12
        step_delay_start = 0.1
        for step in range(step_count):
            circle_chromatic.select_step(step % 12)
            circle_fifths.select_step(step % 12)
            self.wait(step_delay_start * (step_base / (step_base + step)))
        self.wait(1)


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
