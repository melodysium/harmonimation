from typing import Any, TypeVar, Iterable, Iterator, Optional
from fractions import Fraction
import math
import numpy as np
from dataclasses import dataclass

from manim import Mobject, Group, Scene, VDict, PI
from music21.base import Music21Object
from music21.chord import Chord
from music21.key import Key
from music21.note import Note, NotRest, Pitch
from music21.stream import Score, Stream
from music21.common.types import OffsetQL, StreamType
from music21.duration import Duration
from regex import Match

from constants import USE_LATEX
from music import music_constants


# --------------------PYTHON HELPERS--------------------


T = TypeVar("T")


def identity_in(o, it: Iterable) -> bool:
    result = any(e is o for e in it)
    # if result:
    #   print(f"identity_in match! {display_id(o)}, {display_id(it)}")
    return result


def assert_not_none(val: T, err_msg: str = "") -> T:
    assert val is not None, err_msg
    return val


def group_or_default(m: Match, key, default: str) -> str:
    try:
        return m.group(key)
    except IndexError:
        return default


def frange(
    start: float | Fraction, stop: float | Fraction, step: Fraction
) -> Iterator[Fraction]:
    while start < stop:
        yield start
        start += step


def eq_unique(it: Iterable[T]) -> list[T]:
    uniquelist = []
    for obj in it:
        if obj not in uniquelist:
            uniquelist.append(obj)
    return uniquelist


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
    return np.array([math.cos(2 * PI * t), math.sin(2 * PI * t), 0])


def vector_on_unit_circle_clockwise_from_top(t: float):
    return vector_on_unit_circle(1 / 4 - t)


# --------------------MUSIC HELPERS--------------------

M21Obj = TypeVar("M21Obj", bound=Music21Object)

DUMMY_STREAM = Stream()

_rich_accidental_replacements: dict[str, str] = {}
for note in music_constants.Note:
    if note.accidental != 0:
        _rich_accidental_replacements[note.display_portable] = note.display_rich
        _rich_accidental_replacements[note.display_m21] = note.display_rich


@dataclass
class Music21Timing:
    offset: OffsetQL
    duration: Duration

    def apply(self, m21_obj: Music21Object) -> Music21Object:
        m21_obj.offset = self.offset
        m21_obj.duration = self.duration  # TODO: does this need to make a copy?
        return m21_obj


def get_root(m21_chord: Chord) -> Pitch | None:
    if m21_chord is None:
        return None
    if len(m21_chord.pitches) == 0:
        return None
    return m21_chord.root()


def display_chord_short(m21_chord: Chord) -> str:
    replacements = {
        "-major seventh chord": "M7",
        "-minor seventh chord": "m7",
        "-dominant seventh chord": "7",
    }

    if USE_LATEX:
        replacements.update(_rich_accidental_replacements)

    chord_repr = m21_chord.pitchedCommonName
    for repl_old, repl_new in replacements.items():
        chord_repr = chord_repr.replace(repl_old, repl_new)
    return chord_repr


def display_key(m21_key: Key) -> str:
    replacements = {
        "major": "Major",
        "minor": "Minor",
    }
    if USE_LATEX:
        replacements.update(_rich_accidental_replacements)
    key_repr = m21_key.name
    for repl_old, repl_new in replacements.items():
        key_repr = key_repr.replace(repl_old, repl_new)
    return key_repr


def extract_pitches(m21_notRests: Iterable[NotRest]) -> list[Pitch]:
    pitches: set[Pitch] = set()
    for elem in m21_notRests:
        pitches.update(elem.pitches)
    return pitches


def copy_timing(m21_to: M21Obj, timing: Music21Timing) -> M21Obj:
    return timing.apply(m21_to)


def timing_from(m21_from: Music21Object) -> Music21Timing:
    return Music21Timing(
        offset=m21_from.offset,
        duration=m21_from.duration,
    )


def containerInHierarchyByClass(
    elem: Music21Object, root: Stream, classFilter: StreamType
) -> StreamType | None:
    for container in containersInHierarchy(root, elem):
        if isinstance(container, classFilter):
            return container
    return None


def containersInHierarchy(root: Stream, elem: Music21Object) -> Iterator[Stream] | None:
    container = root.containerInHierarchy(elem)
    yield container
    if container is not None and container is not root:
        yield from containersInHierarchy(root, container)


def get_unique_offsets(
    s: Iterable[Music21Object], offsetSite: Stream | None = DUMMY_STREAM
) -> list[OffsetQL]:
    def compute_offset(e: Music21Object) -> OffsetQL:
        if offsetSite is DUMMY_STREAM:
            return e.offset
        return e.getOffsetInHierarchy(offsetSite)

    return sorted(set([compute_offset(e) for e in s]))


# --------------------DISPLAY HELPERS--------------------


def display_note(m21_note: Note) -> str:
    return f"{display_timing(m21_note)}: {m21_note.name:2}{m21_note.octave} ({m21_note.pitch.pitchClass})"


def display_chord(m21_chord: Chord) -> str:
    return f"{display_timing(m21_chord)}: {m21_chord.pitchedCommonName} {m21_chord.fullName}"
    # {m21_chord.root().name} {m21_chord.quality}


def display_notRest(m21_notRest: NotRest) -> str:
    if isinstance(m21_notRest, Note):
        return display_note(m21_notRest)
    elif isinstance(m21_notRest, Chord):
        return display_chord(m21_notRest)
    else:
        raise ValueError("unknown NotRest subclass")


def display_timing(m21_obj: Music21Object, offsetSite: Music21Object) -> str:
    offset = m21_obj.getOffsetInHierarchy(offsetSite) if offsetSite else m21_obj.offset
    return f"@{offset:5} {m21_obj.quarterLength:5} beats"


def display_id(m21_obj: Music21Object) -> str:
    return f"{type(m21_obj)}<{m21_obj.id}>"


def print_notes_stream(notes_stream: Stream[Note], all_elements: bool = False):
    print(notes_stream)
    print(len(notes_stream))
    if all_elements:
        for m21_chord_rootnote in notes_stream:
            print(display_note(m21_chord_rootnote))


def print_chords_stream(chords_stream: Stream[Chord], all_elements: bool = False):
    print(chords_stream)
    print(len(chords_stream))
    if all_elements:
        for m21_chord_rootnote in chords_stream:
            print(display_chord(m21_chord_rootnote))
