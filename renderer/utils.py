from typing import Any, TypeVar, Iterable, Optional
import math
import numpy as np
from dataclasses import dataclass

from manim import Mobject, Group, Scene, VDict, PI
from music21 import chord, note, base, stream
from music21.common.types import OffsetQL
from music21.duration import Duration


# --------------------PYTHON HELPERS--------------------


def identity_in(o, it: Iterable) -> bool:
  result = any(e is o for e in it)
  # if result:
  #   print(f"identity_in match! {display_id(o)}, {display_id(it)}")
  return result



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

M21Obj = TypeVar('M21Obj', bound=base.Music21Object)

@dataclass
class Music21Timing:
  offset: OffsetQL
  duration: Duration

  def apply(self, m21_obj: base.Music21Object) -> base.Music21Object:
    m21_obj.offset = self.offset
    m21_obj.duration = self.duration # TODO: does this need to make a copy?
    return m21_obj



def get_root_note(m21_chord: chord.Chord) -> note.Note:
  return copy_timing(note.Note(m21_chord.root()), timing_from(m21_chord))


def extract_notes(m21_notRestStream: stream.Stream[note.NotRest]) -> stream.Stream[note.Note]:
  # TODO: test offset preservation
  notes: list[note.Note] = []
  for elem in m21_notRestStream:
    if isinstance(elem, note.Note):
      m21_note: note.Note = elem
      notes.append(m21_note)
    elif isinstance(elem, chord.Chord):
      m21_chord: chord.Chord = elem
      notes.extend(m21_chord.notes)
  return copy_timing(stream.Stream(notes), timing_from(m21_notRestStream))


def copy_timing(m21_to: M21Obj, timing: Music21Timing) -> M21Obj:
  return timing.apply(m21_to)


def timing_from(m21_from: base.Music21Object) -> Music21Timing:
  return Music21Timing(
    offset=m21_from.offset,
    duration=m21_from.duration,
  )


def find_direct_owner(elem: base.Music21Object, container: stream.Stream) -> stream.Stream:
    """Finds the Stream which is directly holding the Music21Object specified."""
    # for some reason this method breaks the elem's activeSite, despite `recurse()` having `restoreActiveSites=True`
    activeSite = elem.activeSite
    # print(f"find_direct_owner: elem={display_id(elem)}, container={display_id(container)}. container elements=\n{"\n".join([f"\t{display_id(x)}" for x in container])}")
    # need to check `identity_in(e, x)` because `if e in x` returns true for both parts in a joined PartStaff
    direct_owners = [s for s in container.recurse(includeSelf=True) if isinstance(s, stream.Stream) and identity_in(elem, s)]
    elem.activeSite = activeSite
    assert len(direct_owners) == 1
    return direct_owners[0]


def find_owner(elem: base.Music21Object, containers: list[stream.Stream], error_if_not_found=False) -> Optional[stream.Stream]:
    """Determines which of the specified containers (if any) hold the specified element."""
    # for some reason this method breaks the elem's activeSite, despite `recurse()` having `restoreActiveSites=True`
    activeSite = elem.activeSite
    # need to check `identity_in(e, x)` because `if e in x` returns true for both parts in a joined PartStaff
    container_owners = []
    for c in containers:
      if identity_in(elem, c.recurse()):
        # print(f"find_owner found one possible match: elem={display_id(elem)}, container={display_id(c)}")
        container_owners.append(c)
    # container_owners = [c for c in containers if identity_in(elem, c.recurse())]
    elem.activeSite = activeSite

    if error_if_not_found:
      assert len(container_owners) == 1
      # print(f"find_owner determined exact match: elem={display_id(elem)}, container={display_id(container_owners[0])}")
      return container_owners[0]
    else:
      assert len(container_owners) <= 1
      return container_owners[0] if len(container_owners) == 1 else None


def find_direct_owner_tree(elem: base.Music21Object, container: stream.Stream) -> list[stream.Stream]:
  # print(f"find_direct_owner_tree: elem={display_id(elem)}, container={display_id(container)}")
  # base case
  if elem is container:
    # print("triggered base case!")
    return []
  # recursive case
  direct_owner = find_direct_owner(elem, container)
  direct_owner_tree = [direct_owner]
  direct_owner_tree.extend(find_direct_owner_tree(direct_owner, container))
  return direct_owner_tree


def group_by_offset(s: stream.Stream[base.Music21Object]) -> list[stream.Stream[base.Music21Object]]:
  unique_offsets = sorted(set([e.offset for e in s]))
  return [copy_timing(s.getElementsByOffset(offset, offset).stream(), Music21Timing(offset, Duration(0))) for offset in unique_offsets]


# --------------------DISPLAY HELPERS--------------------


def display_note(m21_note: note.Note) -> str:
  return f"{display_timing(m21_note)}: {m21_note.name:2}{m21_note.octave} ({m21_note.pitch.pitchClass})"


def display_chord(m21_chord: chord.Chord) -> str:
  return f"{display_timing(m21_chord)}: {m21_chord.pitchedCommonName} {m21_chord.fullName}"
  # {m21_chord.root().name} {m21_chord.quality}


def display_notRest(m21_notRest: note.NotRest) -> str:
  if isinstance(m21_notRest, note.Note):
    return display_note(m21_notRest)
  elif isinstance(m21_notRest, chord.Chord):
    return display_chord(m21_notRest)
  else:
    raise ValueError("unknown NotRest subclass")


def display_timing(m21_obj: base.Music21Object) -> str:
   return f"@{m21_obj.offset:5} {m21_obj.quarterLength:5} beats"


def display_id(m21_obj: base.Music21Object) -> str:
  return f"{type(m21_obj)}<{m21_obj.id}>"


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
