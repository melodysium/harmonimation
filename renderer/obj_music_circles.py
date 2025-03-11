#!/usr/bin/env python3.11

# standard libs
import math
from typing import Callable
import logging

# 3rd party libs
from manim import *
from music21 import stream, note
import numpy as np

# my files
from music.music_constants import notes_in_sequence
from obj_music_text import TextNote
from utils import vector_on_unit_circle_clockwise_from_top

# log setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LabelledCircle(VGroup):

  def __init__(self, circle_color=RED, text="Circle", **kwargs):
    VGroup.__init__(self, **kwargs)
    self.circle_color = circle_color
    self.circle = Circle(color=circle_color)
    self.text = Text(text=text)
    self.add(self.circle)
    self.add(self.text)
  
  def create(self):
    return AnimationGroup(
      Create(self.circle),
      Create(self.text),
      lag_ratio=0.5
    )


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
BASE_NOTE_LABEL_FONT_SIZE = 16
BASE_NOTE_CIRCLE_RADIUS = 0.2
class Circle12NotesBase(VGroup):

  # mobjects
  mob_circle_background: Circle
  mob_notes: VDict # VDict[int, TextNote]
  mob_select_circles: VDict # VDict[int, Circle]

  # properties
  circle_color: str
  radius: float

  def __init__(
      self,
      circle_color=GRAY,
      radius: float=1,
      note_intervals: int=1,
      **kwargs
  ):
    VGroup.__init__(self, **kwargs)
    # save properties
    self.circle_color = circle_color
    self.radius = radius

    # add background circle
    self.mob_circle_background = Circle(color=circle_color, radius=radius, stroke_opacity=0.3, stroke_width=8).flip().rotate(-90 * (PI / 180))
    self.add(self.mob_circle_background)
    # set up notes
    self.mob_notes = VDict()
    self.add(self.mob_notes)
    self.mob_select_circles = VDict()
    self.add(self.mob_select_circles)
    # create 12 individual notes and small highlight circles
    for note_idx, note in enumerate(notes_in_sequence(note_intervals)):
      # calculate position
      offset = vector_on_unit_circle_clockwise_from_top(note_idx / 12)
      # create TextNote and circle in correct position
      note_label = TextNote(note, font_size=BASE_NOTE_LABEL_FONT_SIZE*radius).shift(offset * radius)
      note_circle = Circle(color=WHITE, radius=BASE_NOTE_CIRCLE_RADIUS*radius, stroke_opacity=0).move_to(note_label)
      # save mobjects, add note text
      self.mob_notes[note.scale_step] = note_label
      self.mob_select_circles[note.scale_step] = note_circle

  # TODO: fix bug where self isn't created, but all its submobjects are
  def create(self) -> Animation:
    return AnimationGroup(
      Create(self.mob_circle_background, rate_func=rate_functions.ease_in_sine),
      AnimationGroup(
        Create(self.mob_notes),
        Create(self.mob_select_circles),
      ),
      lag_ratio=0.18
    )
  
  def highlight_step(self, step: int, opacity: float):
    """Sets the highlight circle around the note text for a given step to the specified opacity."""
    note_circle = self.mob_select_circles[step]
    note_circle.set_stroke(opacity=opacity)
  
  def play_notes(stream: stream.Stream, bpm: int) -> Animation:
    bps = bpm / 60

    pass # TODO: implement


class PlayCircle12NotesV2(Animation):

  # beats per second
  bps: float
  total_beats: float
  notes: stream.Stream[note.Note]
  last_processed_step: float
  circle12: Circle12NotesBase
  played: set

  def __init__(self, bpm: float, notes: stream.Stream, circle12: Circle12NotesBase, **kwargs):
    self.bps = bpm / 60
    self.total_beats = notes.highestTime
    super().__init__(circle12, run_time=self.total_beats / self.bps, **kwargs)
    self.notes = notes
    self.last_processed_step = -1
    self.circle12 = circle12
    self.played = set()

  
  def interpolate_mobject(self, alpha: float):
    current_step = alpha * self.total_beats
    new_note: note.Note
    for new_note in self.notes.getElementsByOffset(self.last_processed_step, current_step, includeElementsThatEndAtStart=False):
      if new_note not in self.played:
        logger.debug(f"iteration of PlayCircle12Notes, current_step={current_step}")
        logger.debug(f"processing new_note {new_note.offset:5} {new_note.name}")
        self.circle12.select_step(new_note.pitch.pitchClass)
        self.played.add(new_note)
    self.last_processed_step = current_step


class Circle12NotesSequenceConnectors(Circle12NotesBase):

  # mobjects
  mob_select_connectors: VGroup
  hack_select_connectors: list[Line]

  # properties
  max_selected_steps: int
  calculate_circle_opacity: Callable[[int, int], float]

  def calculate_circle_opacity_default(select_idx: int, max_selected_steps: int) -> float:
    pct = select_idx / max_selected_steps
    return (1 - pct)**1.5

  # implementation details
  _selected_steps: list[int]

  def __init__(
      self,
      circle_color=GRAY,
      radius: float=1,
      note_intervals: int=1,
      max_selected_steps: int=3,
      select_circle_opacity=calculate_circle_opacity_default,
      **kwargs
  ):
    Circle12NotesBase.__init__(self, circle_color, radius, note_intervals, **kwargs)
    # initialize fields
    self._selected_steps = []
    self.hack_select_connectors = [] # TODO: figure out a better hack. maybe subclass VGroup?
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
        Create(self.mob_notes),
        Create(self.mob_select_circles),
        Create(self.mob_select_connectors),
      ),
      lag_ratio=0.18
    )
    
  def select_step(self, step: int):
    logger.debug(f"  invoke select_step({step}); {self._selected_steps=}, {self.max_selected_steps}, {self.hack_select_connectors}: ", end='')
    
    # if already selected, ignore
    if self._selected_steps and step is self._selected_steps[0]:
      logger.debug(f"ignoring redundant select_step({step}); already selected")
      return

    # mark this note as selected
    self._selected_steps.insert(0, step)

    # if there is a previous selected note, add a connector
    if len(self._selected_steps) >= 2:
      # TODO: maybe check if this connector already exists?
      # get circle centers
      new_select_circle = self.mob_select_circles[self._selected_steps[0]]
      prev_select_circle = self.mob_select_circles[self._selected_steps[1]]
      # create connector line
      mob_connector = get_line_between_two_circle_edges(prev_select_circle, new_select_circle)
      # mob_connector = get_line_between_two_circle_edges(*(self.mob_select_circles[self._selected_steps[idx]] for idx in range(2)))
      # add connector to shape
      self.hack_select_connectors.insert(0, mob_connector)
      self.mob_select_connectors.add(mob_connector)
      # self.add(mob_connector) # TODO: had this, commented it out to fix a bug. can probably remove?

    # if we're over our limit, un-select an old step and make it invisible
    if len(self._selected_steps) > self.max_selected_steps:
      # remove the circle
      old_step: int = self._selected_steps.pop()
      self.highlight_step(step=old_step, opacity=0)
      # remove the oldest connector
      old_select_connector = self.hack_select_connectors.pop()
      self.mob_select_connectors.remove(old_select_connector)

    # update opacities for all remaining select circles and connectors
    # reversed() starts at the oldest (dimmest) circle, so that if it's also selected in a newer step, that one is used instead
    for select_idx, select_step in reversed(list(enumerate(self._selected_steps))):
      new_opacity = self.calculate_circle_opacity(select_idx, self.max_selected_steps)
      self.highlight_step(step=select_step, opacity=new_opacity)
      # dont update a connector that doesn't exist
      if select_idx != len(self._selected_steps) - 1:
        mob_select_connector = self.hack_select_connectors[select_idx]
        mob_select_connector.set_stroke(opacity=new_opacity)
    return self


class PlayCircle12Notes(Animation):

  # beats per second
  bps: float
  total_beats: float
  notes: stream.Stream[note.Note]
  last_processed_step: float
  circle12: Circle12NotesSequenceConnectors
  played: set

  def __init__(self, bpm: float, notes: stream.Stream, circle12: Circle12NotesSequenceConnectors, **kwargs):
    self.bps = bpm / 60
    self.total_beats = notes.highestTime
    super().__init__(circle12, run_time=self.total_beats / self.bps, **kwargs)
    self.notes = notes
    self.last_processed_step = -1
    self.circle12 = circle12
    self.played = set()

  
  def interpolate_mobject(self, alpha: float):
    current_step = alpha * self.total_beats
    new_note: note.Note
    for new_note in self.notes.getElementsByOffset(self.last_processed_step, current_step, includeElementsThatEndAtStart=False):
      if new_note not in self.played:
        logger.debug(f"iteration of PlayCircle12Notes, current_step={current_step}")
        logger.debug(f"processing new_note {new_note.offset:5} {new_note.name}")
        self.circle12.select_step(new_note.pitch.pitchClass)
        self.played.add(new_note)
    self.last_processed_step = current_step





# class AddNoteCircle(Animation):
#   def __init__(self, circle_12_notes: Circle12Notes, )


class test(Scene):
  def construct(self):
    self.wait(0.2)
    circle_chromatic = Circle12NotesSequenceConnectors(radius=1.5).shift(2 * LEFT)
    circle_fifths = Circle12NotesSequenceConnectors(radius=1.5, note_intervals=7).shift(2 * RIGHT)
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
    circle_fifths = Circle12NotesSequenceConnectors(radius=1.5, note_intervals=7).shift(2 * RIGHT)
    self.play(circle_chromatic.create(), circle_fifths.create(), run_time=2)
    self.wait(1)

    # duration.Duration()

    melody = stream.Stream([
      note.Note("C", quarterLength=2),
      note.Note("F", quarterLength=2),
      note.Note("B-", quarterLength=2),
      note.Note("E-", quarterLength=2),
      note.Note("C", quarterLength=2),
      note.Note("F", quarterLength=2),
      note.Note("G", quarterLength=2.75),
      note.Note("C", quarterLength=1.25),
    ])

    play_circle_chromatic = PlayCircle12Notes(bpm=128, notes=melody, circle12=circle_chromatic)
    play_circle_fifths = PlayCircle12Notes(bpm=128, notes=melody, circle12=circle_fifths)
    self.play(AnimationGroup(
      play_circle_chromatic,
      play_circle_fifths,
      ))