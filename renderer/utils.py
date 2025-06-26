from typing import Any, TypeVar, Iterable, Iterator, Optional
from fractions import Fraction
import math
import numpy as np
from dataclasses import dataclass

from manim import (
    Mobject,
    Group,
    Scene,
    VDict,
    PI,
    Animation,
    Wait,
    Succession,
    Circle,
    TAU,
    ManimColor,
    Dot,
    WHITE,
)
from manim.typing import Point3D
from music21.base import Music21Object
from music21.chord import Chord
from music21.interval import Interval
from music21.key import Key
from music21.note import Note, NotRest
from music21.pitch import Pitch
from music21.stream import Score, Stream
from music21.common.types import OffsetQL, StreamType
from music21.duration import Duration
from regex import Match

from constants import USE_LATEX
from music import music_constants

print(f"{USE_LATEX=}")

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


def stable_unique(it: Iterable[T]) -> list[T]:
    return list(dict.fromkeys(it))


def generate_group(start: int, step: int, size: int) -> list[int]:
    return stable_unique((start + i * step) % size for i in range(size))


# --------------------MANIM HELPERS--------------------


def callback_add_to_group(group: Group, object: Mobject):
    def callback(_: Scene) -> None:
        group.add(object)

    return callback


def callback_add_to_vdict(vdict: VDict, index: Any, object: Mobject):
    def callback(_: Scene) -> None:
        vdict[index] = object

    return callback


def point_at_angle(circle: Circle, angle: float) -> Point3D:
    proportion = (angle) / TAU
    proportion -= np.floor(proportion)
    return circle.point_from_proportion(proportion)


class TimestampedAnimationSuccession(Succession):
    """Given a list of animations which should each end at a particular time,
    create a Succession of all of them separated by Wait animations."""

    def __init__(
        self,
        anims: list[
            tuple[float, Animation]
        ],  # list[end_timestamp: second, anim: Animation]
        transition_time: float,
        **kwargs,
    ):
        # build a sequence of animations to play - waits followed by rotations
        sequenced_anims: list[Animation] = []
        # previous_pitch_class: int = get_ionian_root(music_data.keys[0].elem).pitchClass
        previous_time: float = 0

        for anim_timestamp, anim in anims:

            # print(
            #     f"TimestampedAnimationSuccession step:\n\t{previous_time=}\n\t{anim_timestamp}, {anim}"
            # )

            # fiture out how long since last update
            assert anim_timestamp > previous_time
            elapsed_time = anim_timestamp - previous_time

            # if we don't have time to do a full wait-then-transition
            if elapsed_time <= transition_time:
                # just animate with the time we have
                anim.run_time = elapsed_time
                sequenced_anims.append(anim)
            else:
                # sleep until start of time when we need to transform
                sequenced_anims.append(Wait(elapsed_time - transition_time))
                anim.run_time = transition_time
                sequenced_anims.append(anim)
            # done processing this animation
            previous_time = anim_timestamp

        super().__init__(sequenced_anims, **kwargs)


class Anchor(Dot):

    def __init__(
        self,
        point: Point3D,
        fill_opacity: int = 0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, point=point, fill_opacity=fill_opacity, **kwargs)

    def add_follower(self, mobject: Mobject) -> "Anchor":
        def follow_anchor(follower: Mobject):
            anchor_pos = self.get_center()[0:2]
            follower_before_pos = follower.get_center()[0:2]
            follower.move_to(self)
            if follower.text == "East":
                follower_after_pos = follower.get_center()[0:2]
                print(
                    f"follow_anchor({follower}):\n\t       anchor: {anchor_pos}\n\tfollow_before: {follower_before_pos}\n\t follow_after: {follower_after_pos}"
                )

        mobject.add_updater(follow_anchor, call_updater=True)
        return self


# --------------------MATH HELPERS--------------------


# TODO: use Circle.point_at_angle?
def vector_on_unit_circle(t: float):
    return np.array([math.cos(2 * PI * t), math.sin(2 * PI * t), 0])


def vector_on_unit_circle_clockwise_from_top(t: float):
    return vector_on_unit_circle(1 / 4 - t)


def pick_preferred_rotation(start_angle, end_angle) -> float:
    """Pick the shorter rotation from start to end angle (in unit rotations)"""
    angle_diff = (end_angle - start_angle) % 1
    if angle_diff <= 0.5:
        return angle_diff
    else:
        return angle_diff - 1


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


def get_chord_root(m21_chord: Chord) -> Pitch | None:
    if m21_chord is None:
        return None
    if len(m21_chord.pitches) == 0:
        return None
    return m21_chord.root()


def get_key_tonic(m21_key: Key) -> Pitch:
    tonic = m21_key.getTonic()
    assert tonic is not None
    return tonic


def get_ionian_root(m21_key: Key) -> Pitch:
    return get_key_tonic(m21_key.asKey(mode="ionian"))


def display_chord_short_custom(m21_chord: Chord) -> str | None:
    quality_mapping = {
        "augmented": "+",
        "major": "Maj",
        "minor": "min",
        "diminished": "dim",
        "half-diminished": "ø",
        "full-diminished": "°",
    }

    if not m21_chord.isChord or len(m21_chord.pitches) < 3:
        return "no chord"  # TODO: handle other cases

    chord_root = m21_chord.root()
    chord_root_str = chord_root.name
    # print(
    #     f"display_chord_short_custom(): {chord_root=}, {m21_chord.pitches=}, {m21_chord.pitchedCommonName=}"
    # )

    def steps_above_root(m21_pitch: Pitch = None, pitchClass: int = None) -> int:
        if m21_pitch is not None:
            pitchClass = m21_pitch.pitchClass
        if pitchClass is None:
            raise ValueError("must provide either pitch or pitchClass")
        return (pitchClass - chord_root.pitchClass) % 12

    if m21_chord.isTriad():  # 3 notes
        # print("it's a triad")
        quality = m21_chord.quality
        quality_str = quality_mapping.get(quality, quality)
        return f"{chord_root_str}{quality_str}"
    # elif m21_chord.isSeventh() or m21_chord.isNinth():  # 4-5 notes
    # TODO: assume everything else is a 7th or 9th chord
    else:
        third_steps = steps_above_root(m21_chord.third)
        fifth_steps = steps_above_root(m21_chord.fifth)
        seventh_steps = steps_above_root(m21_chord.seventh)
        match (third_steps, fifth_steps, seventh_steps):
            case (4, 7, 11):
                quality_str = "Maj7"  # major 7
            case (3, 7, 11):
                quality_str = "mM7"  # minor-major 7
            case (4, 7, 10):
                quality_str = "7"  # dominant
            case (3, 7, 10):
                quality_str = "min7"  # minor 7
            case (3, 6, 10):
                quality_str = "ø7"  # half-diminished # TODO: or maybe "b5b7"?
            case (3, 6, 9):
                quality_str = "°7"  # fully-diminished
        # print(f"{third_steps=}, {fifth_steps=}, {seventh_steps=}, 7th quality={quality_str}")

        # figure out how to display other pitches in the chord
        other_pitches = {
            steps_above_root(pitch): pitch
            for pitch in m21_chord.pitches
            if pitch.pitchClass
            not in (
                chord_root.pitchClass,
                m21_chord.third.pitchClass,
                m21_chord.fifth.pitchClass,
                m21_chord.seventh.pitchClass,
            )
        }

        if len(other_pitches) > 0:
            # hack for now - handle known cases.
            # TODO: handle weirder stuff later.

            # handle ninth pitches
            ninth_pitches = {
                step: p for step, p in other_pitches.items() if step == 1 or step == 2
            }
            # print(f"{other_pitches=}, {ninth_pitches=}")
            if m21_chord.isNinth() or len(ninth_pitches) == 1:
                assert (
                    len(ninth_pitches) == 1
                )  # TODO: handle sharp ninths later if that's a thing I care about?
                ninth_steps_above_root, _ = list(ninth_pitches.items())[0]
                if ninth_steps_above_root == 1:
                    quality_str += "♭9"
                elif ninth_steps_above_root == 2:
                    assert quality_str in ("Maj7", "7", "min7")
                    quality_str = quality_str.replace("7", "9")

                del other_pitches[ninth_steps_above_root]

            # process remaining extra pitches
            for step, pitch in other_pitches.items():
                # add6
                if step == 9:
                    quality_str += "add6"
                else:
                    # give up, use music21's name
                    return None

    # Add note name to chord quality
    return f"{_rich_accidental_replacements.get(chord_root_str, chord_root_str)}{quality_str}"


def display_chord_short(m21_chord: Chord) -> str:

    # first: try to display a name using my custom logic
    chord_repr = display_chord_short_custom(m21_chord)
    if chord_repr is not None:
        return chord_repr

    # otherwise, adapt from Music21's names
    chord_repr = m21_chord.pitchedCommonName
    replacements = {
        "-major seventh chord": "M7",
        "-minor seventh chord": "m7",
        "-dominant seventh chord": "7",
    }

    if USE_LATEX:
        replacements.update(_rich_accidental_replacements)

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
