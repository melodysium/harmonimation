

# standard libs
import math
from typing import Dict, List, Set, Union, Callable

# 3rd party libs
from manim import *
import numpy as np

# my files
from music.music_constants import notes_in_sequence
from music_text import TextNote


class LabelledCircle(VGroup):

  def __init__(self, circle_color=RED, text="Circle", **kwargs):
    VGroup.__init__(self, **kwargs)
    self.circle_color = circle_color
    self.add(Circle(color=circle_color))
    self.add(Text(text=text))


def vector_on_unit_circle(t: float):
  return np.array([math.cos(2*PI*t), math.sin(2*PI*t), 0])

def vector_on_unit_circle_clockwise_from_top(t: float):
  return vector_on_unit_circle(1/4 - t)

def get_line_between_two_circle_edges(c1: Circle, c2: Circle):
  direction = Line(c1.get_center(), c2.get_center()).get_unit_vector()
  c1_point = c1.get_center() + direction * c1.radius
  c2_point = c2.get_center() - direction * c2.radius
  return Line(c1_point, c2_point)


class Circle12Notes(VGroup):

  # mobjects
  mob_circle_background: Circle
  mob_notes: Dict[int, TextNote]
  mob_select_circles: Dict[int, Circle]
  mob_select_connectors: List[Line]

  # properties
  circle_color: str
  radius: float
  max_selected_steps: int
  select_circle_opacity: Callable[[int, int], float]

  def select_circle_opacity_default(select_idx: int, max_selected_steps: int) -> float:
    pct = select_idx / max_selected_steps
    return (1 - pct)**1.5

  # implementation details
  _selected_steps: List[int]

  def __init__(self, circle_color=GRAY, radius: float=1,
      note_intervals: int=1, max_selected_steps: int=3,
      select_circle_opacity=select_circle_opacity_default, **kwargs):
    VGroup.__init__(self, **kwargs)
    # save properties
    self.circle_color = circle_color
    self.radius = radius
    self.max_selected_steps = max_selected_steps
    self.select_circle_opacity = select_circle_opacity

    # add background circle
    self.add(Circle(color=circle_color, radius=radius, stroke_opacity=0.3, stroke_width=8))
    # set up notes and selectors
    self._selected_steps = []
    self.mob_notes = {}
    self.mob_select_circles = {}
    self.mob_select_connectors = []
    for note_idx, note in enumerate(notes_in_sequence(note_intervals)):
      # calculate position
      offset = vector_on_unit_circle_clockwise_from_top(note_idx / 12)
      # create TextNote and circle in correct position
      note_text = TextNote(note, font_size=18*radius).shift(offset * radius)
      note_circle = Circle(color=WHITE, radius=0.15*radius, stroke_opacity=0).move_to(note_text)
      # save mobjects, add note text
      self.mob_notes[note.scale_step] = note_text
      self.mob_select_circles[note.scale_step] = note_circle
      self.add(note_text)
      # print(note_circle.get_center())
      # print(self.get_center())
      self.add(note_circle)
      
    
  def select_step(self, step: int):
    
    # if already selected, ignore
    if step in self._selected_steps:
      print(f"ignoring redundant select_step({step}); already selected")
      return

    # mark this note as selected
    self._selected_steps.insert(0, step)

    # if there is a previous selected note, add a connector
    if len(self._selected_steps) >= 2:
      new_select_circle = self.mob_select_circles[self._selected_steps[0]]
      prev_select_circle = self.mob_select_circles[self._selected_steps[1]]
      # mob_connector = Line(new_select_circle.get_center(), prev_select_circle.get_center())
      mob_connector = get_line_between_two_circle_edges(prev_select_circle, new_select_circle)
      self.mob_select_connectors.insert(0, mob_connector)
      self.add(mob_connector)

    # if we're over our limit, un-select an old step and make it invisible
    if len(self._selected_steps) > self.max_selected_steps:
      # remove the circle
      old_step: int = self._selected_steps.pop()
      old_selection_circle = self.mob_select_circles[old_step]
      old_selection_circle.set_stroke(opacity=0)
      # remove the oldest connector
      old_select_connector = self.mob_select_connectors.pop()
      self.remove(old_select_connector)

    # update opacities for all remaining select circles and connectors
    for select_idx, select_step in enumerate(self._selected_steps):
      note_circle = self.mob_select_circles[select_step]
      note_circle.set_stroke(opacity=self.select_circle_opacity(select_idx, self.max_selected_steps))
      # dont update a connector that doesn't exist
      if select_idx != len(self._selected_steps) - 1:
        mob_select_connector = self.mob_select_connectors[select_idx]
        mob_select_connector.set_stroke(opacity=self.select_circle_opacity(select_idx, self.max_selected_steps))
    return self


# class AddNoteCircle(Animation):
#   def __init__(self, circle_12_notes: Circle12Notes, )


class test(Scene):
  def construct(self):
    self.wait(0.2)
    circle_chromatic = Circle12Notes(radius=1.5).shift(2 * LEFT)
    circle_fifths = Circle12Notes(radius=1.5, note_intervals=7).shift(2 * RIGHT)
    self.play(Create(circle_chromatic), Create(circle_fifths), run_time=2)
    self.wait(1)
    step_count = 12 * 8 + 1
    step_base = 12
    step_delay_start = 0.8
    for step in range(step_count):
      circle_chromatic.select_step(step % 12)
      circle_fifths.select_step(step % 12)
      self.wait(step_delay_start * (step_base / (step_base + step)))
    self.wait(1)