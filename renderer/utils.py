from typing import Any
import math
import numpy as np

from manim import Mobject, Group, Scene, VDict, PI
from music21 import chord, note

from music21 import stream


# --------------------MANIM HELPERS--------------------


def callback_add_to_group(group: Group, object: Mobject):
    def callback(_: Scene) -> None:
        group.add(object)
    return callback


def callback_add_to_vdict(vdict: VDict, index: Any, object: Mobject):
    def callback(_: Scene) -> None:
        vdict[index] = object
    return callback


# --------------------MATH HELPERS--------------------


# TODO: use Circle.point_at_angle?
def vector_on_unit_circle(t: float):
  return np.array([math.cos(2*PI*t), math.sin(2*PI*t), 0])


def vector_on_unit_circle_clockwise_from_top(t: float):
  return vector_on_unit_circle(1/4 - t)


# --------------------MUSIC HELPERS--------------------


def get_root_note(m21_chord: chord.Chord) -> note.Note:
  m21_note = note.Note(m21_chord.root())
  m21_note.duration = m21_chord.duration
  m21_note.offset = m21_chord.offset
  return m21_note


# --------------------DISPLAY HELPERS--------------------


def display_note(m21_note: note.Note) -> str:
  return f"@{m21_note.offset:5} {m21_note.duration.quarterLength:5} beats: {m21_note.name:2}{m21_note.octave} ({m21_note.pitch.pitchClass})"


def display_chord(m21_chord: chord.Chord) -> str:
  return f"@{m21_chord.offset:5} {m21_chord.duration.quarterLength:5} beats: {m21_chord.pitchedCommonName} {m21_chord.fullName}"
  # {m21_chord.root().name} {m21_chord.quality}


def print_notes_stream(notes_stream: stream.Stream[note.Note], all_elements: bool=False):
  print(notes_stream)
  print(len(notes_stream))
  if all_elements:
    for m21_chord_rootnote in notes_stream:
      print(display_note(m21_chord_rootnote))


def print_chords_stream(chords_stream: stream.Stream[chord.Chord], all_elements: bool=False):
  print(chords_stream)
  print(len(chords_stream))
  if all_elements:
    for m21_chord_rootnote in chords_stream:
      print(display_chord(m21_chord_rootnote))
