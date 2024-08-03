

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


class Circle12Notes(VGroup):

  def __init__(self, circle_color=GRAY, radius: float=1, note_intervals: int=1, **kwargs):
    VGroup.__init__(self, **kwargs)
    self.circle_color = circle_color
    self.add(Circle(color=circle_color, radius=radius, stroke_opacity=0.3, stroke_width=8))

    for note_idx, note in enumerate(notes_in_sequence(note_intervals)):
      note_text = TextNote(note, font_size=24*radius)
      offset = vector_on_unit_circle_clockwise_from_top(note_idx / 12)
      note_text.shift(offset * radius)
      self.add(note_text)


class test(Scene):
  def construct(self):
    self.wait(0.2)
    circle_chromatic = Circle12Notes(radius=1.5).shift(2 * LEFT)
    circle_fifths = Circle12Notes(radius=1.5, note_intervals=7).shift(2 * RIGHT)
    self.play(Create(circle_chromatic), Create(circle_fifths), run_time=2)
    self.wait()