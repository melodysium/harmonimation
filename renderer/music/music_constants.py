from enum import Enum, auto
from typing import Iterable

class Accidental(Enum):
  def __new__(cls, *args, **kwds):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj
  DOUBLE_FLAT = 0
  FLAT = 1
  NATURAL = 2
  SHARP = 3
  DOUBLE_SHARP = 4


class Note(Enum):
  def __new__(cls, *args, **kwds):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj
  def __init__(self, scale_step: int, accidental: int, degree: int, display: str):
    self.scale_step = scale_step
    self.display = display
    self.accidental = accidental
  def __repr__(self) -> str:
    return self.display
  # naturals and flats
  Cb = 11, -1, 0, 'Cb'
  C  = 0,  0,  0, 'C'
  Cs = 1,  1,  0, 'C#'
  Db = 1,  -1, 1, 'Db'
  D  = 2,  0,  1, 'D'
  Ds = 3,  1,  1, 'D#'
  Eb = 3,  -1, 2, 'Eb'
  E  = 4,  0,  2, 'E'
  Es = 5,  1,  2, 'E#'
  Fb = 4,  -1, 3, 'Fb'
  F  = 5,  0,  3, 'F'
  Fs = 6,  1,  3, 'F#'
  Gb = 6,  -1, 4, 'Gb'
  G  = 7,  0,  4, 'G'
  Gs = 8,  1,  4, 'G#'
  Ab = 8,  -1, 5, 'Ab'
  A  = 9,  0,  5, 'A'
  As = 10, 1,  5, 'A#'
  Bb = 10, -1, 6, 'Bb'
  B  = 11, 0,  6, 'B'
  Bs = 0,  1,  6, 'B#'
# create map of notes by step
_notes_by_step = {
  step: {note.accidental: note for note in Note if note.scale_step == step}
  for step in range(12)
}
# link enharmonics
for step in range(12):
  enharmonics = _notes_by_step[step]
  if len(enharmonics) == 2:
    note_lower, note_higher = enharmonics.values()
    note_lower.enharmonic = note_higher
    note_higher.enharmonic = note_lower
  else:
    enharmonics[0].enharmonic = None


def note_for_step(step: int):
  note_options = _notes_by_step[step]
  if 0 in note_options: # if natural, use that
    return note_options[0]
  else:
    return note_options[min(note_options)]
  return [0 if prefer_flat else -1]


def notes_for_steps(steps: Iterable) -> list:
  return [note_for_step(step) for step in steps]


def IntervalQuality(Enum):
  def __new__(cls, *args, **kwds):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj
  def __init__(self, note_offset: int, display_char: str, display_str: str):
    self.display_char = display_char
    self.display_str = display_str
  DIMINISHED = -1, 'd', "Diminished"
  MINOR      = 0,  'm', "Minor"
  PERFECT    = 0,  'P', "Perfect"
  MAJOR      = 0,  'M', "Major"
  AUGMENTED  = 1,  'A', "Augmented"
  

def interval_exact(note_from: Note, step_offset: int):
  desired_step = (note_from.scale_step + step_offset) % 12
  return note_for_step(desired_step)

def notes_in_sequence(step_offset: int=1, step_start: int=0):
  step_sequence = [(step_start + step * step_offset) % 12 for step in range(12)]
  step_sequence_unique = list(dict.fromkeys(step_sequence))
  note_sequence = [note_for_step(step) for step in step_sequence_unique]
  return note_sequence


if __name__ == '__main__':
  for step, notes in _notes_by_step.items():
    print(f"{step:>2}: " + str(notes))
  print(notes_in_sequence(7))