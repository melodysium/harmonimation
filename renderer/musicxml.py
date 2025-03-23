# std library
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import groupby
from typing import Callable

# 3rd party library
from music21 import converter
from music21.base import Music21Object
from music21.chord import Chord
from music21.common.types import OffsetQL
from music21.harmony import ChordSymbol, NoChord
from music21.note import Note, NotRest
from music21.stream import Stream, Score, Part, Measure
import regex as re  # stdlib re doesn't support multiple named capture groups with the same name, i use it below

# project files
from utils import (
    extract_notes_with_offset,
    extract_pitches,
    get_root,
    copy_timing,
    timing_from,
    get_unique_offsets,
    assert_not_none,
    group_or_default,
    frange,
)
from utils import (
    print_notes_stream,
    display_timing,
    display_chord,
    display_notRest,
    display_id,
)

# TODO: replace 'a' with a different letter since 'a' is a valid chord :(
DEFAULT_CHORD_SYMBOL = ChordSymbol(kindStr="ma")


# data transfer class
@dataclass
class MusicData:
    # new ones
    chords: list[tuple[OffsetQL, Chord]]
    all_notes: list[tuple[OffsetQL, Note]]
    all_notes_by_part: dict[Part, list[tuple[OffsetQL, NotRest]]] = None  # TODO: fill
    bpm: object = None  # TODO: what would this look like?
    current_key: object = None  # TODO: what would this look like?
    lyrics: object = None  # TODO: what would this look like?
    comments: object = None  # TODO: what would this look like?

    def __init__(self, m21_score: Score):
        # new ones
        self.all_notes = extract_notes_with_offset(m21_score)
        self.all_notes_by_part = {
            part: extract_notes_with_offset(part) for part in m21_score.parts
        }
        self.chords = extract_harmonic_clusters(m21_score)


def extract_chord_symbols(m21_score: Score) -> tuple[
    # non-`x` chord symbol per part per offset
    list[
        tuple[
            OffsetQL,
            dict[Part, ChordSymbol],
        ]
    ],
    # list[
    #     tuple[
    #         OffsetQL,
    #         # parts at this offset with an `x`
    #         set[Part],
    #     ]
    # ],
    # list of specific offsets to exclude per part
    dict[Part, list[OffsetQL]],
]:
    # (global offset, chordSymbol, part) for all chordSymbols in the score
    chord_symbol_info = sorted(
        (
            (chord_symbol.getOffsetInHierarchy(part), chord_symbol, part)
            for part in m21_score.parts
            for chord_symbol in part.recurse().getElementsByClass(ChordSymbol)
        ),
        key=lambda t: t[0],
    )

    # identify all non-`x` chord symbols
    harmonic_span_chord_symbol_info = list(
        filter(lambda t: t[1].chordKindStr.lower() != "x", chord_symbol_info)
    )
    # group chord symbols by offset
    grouped_chord_symbols = groupby(
        harmonic_span_chord_symbol_info, key=lambda csi: csi[0]
    )
    # make a tuple of all ChordSymbols-by-Part at each offset
    chord_symbols_per_part_per_offset: list[
        tuple[OffsetQL, dict[Part, ChordSymbol]]
    ] = []
    for offset, chord_symbol_info_iter in grouped_chord_symbols:
        # add (offset, {part: chordSymbol})
        chord_symbols_per_part_per_offset.append(
            (offset, {csi[2]: csi[1] for csi in chord_symbol_info_iter})
        )
    # if no chord symbol in first measure, insert a default one
    if (
        len(chord_symbols_per_part_per_offset) == 0
        or chord_symbols_per_part_per_offset[0][0] > 0
    ):
        chord_symbols_per_part_per_offset.insert(
            0, (0.0, {m21_score.parts.first(): DEFAULT_CHORD_SYMBOL})
        )

    # # identify all the `x` chord symbols
    # x_chord_symbols_by_part = list(
    #     filter(lambda t: t[1].chordKindStr.lower() == "x", chord_symbol_info)
    # )
    # # get a list of all unique offsets
    # x_unique_offsets = get_unique_offsets(
    #     [t[1] for t in x_chord_symbols_by_part], offsetSite=m21_score
    # )
    # # for each unique offset, make a set of all Parts with an x at that offset
    # parts_with_x_per_offset = [
    #     (
    #         offset,
    #         {
    #             t[0]
    #             for t in x_chord_symbols_by_part
    #             if t[1].getOffsetInHierarchy(m21_score) == offset
    #         },
    #     )
    #     for offset in x_unique_offsets
    # ]

    # group the `x` symbols by part
    x_offsets_per_part = defaultdict(lambda: [])
    for _, part, chord_symbol in chord_symbol_info:
        x_offsets_per_part[part].append(chord_symbol.getOffsetInHierarchy(m21_score))

    return (
        chord_symbols_per_part_per_offset,
        # parts_with_x_per_offset,
        x_offsets_per_part,
    )


def analyze_harmonic_cluster(notes: Stream[Note]) -> Chord:
    return copy_timing(Chord(set(n.pitch for n in notes)), timing_from(notes))


def _build_chord_annotation_pattern() -> re.Pattern:
    float_restr = r"([0-9]*[.])?[0-9]+"
    # how often to process a new chord. n = "never", m = "measure", <number> = <number> beats
    harmonic_rhythm = rf"(?P<harmonic_rhythm>n|m|{float_restr})"
    # which parts to include in harmonic analysis
    harmonic_parts = rf"(?P<harmonic_parts>[pa])"
    # require at least one of these, in order
    harmonic_span = rf"({harmonic_rhythm}{harmonic_parts}?|{harmonic_parts})"
    # final chord annotation pattern
    chord_annotation = rf"^{harmonic_span}$"
    return re.compile(chord_annotation)


CHORD_ANNOTATION_PATTERN = _build_chord_annotation_pattern()


def _test_chord_annotation_pattern():
    matches = [
        "ma",
        "m",
        "a",
        "np",
        "n",
        "p",
        "6",
        "1.5",
        ".5",
    ]
    for s in matches:
        assert CHORD_ANNOTATION_PATTERN.match(s) is not None, f"should accept {s}"
    rejects = [
        "xa",
        "",
        "mm",
        "aa",
        "am",
        "b",
        "ba",
    ]
    for s in rejects:
        assert CHORD_ANNOTATION_PATTERN.match(s) is None, f"should reject {s}"


# _test_chord_annotation_pattern()


def process_chord_annotation(
    m21_score: Score,
    range: tuple[OffsetQL, OffsetQL],
    chord_symbols: dict[Part, ChordSymbol],
    x_symbols_2: dict[Part, list[OffsetQL]],
) -> list[tuple[OffsetQL, Chord]]:

    # Easy case: Chord is hard-coded
    if len([cs for cs in chord_symbols.values() if not isinstance(cs, NoChord)]):
        # Validation: If manual chord is set, it should be alone
        if len(chord_symbols) > 1:
            raise ValueError(
                "Invalid annotation - cannot have manual chord set in the same beat as any other chord annotations."
            )
        return [(range[0], next(chord_symbols.values()))]

    # Complicated case: Parse the NoChords
    # --------parsing--------
    parsed_chord_symbols = {
        part: assert_not_none(
            CHORD_ANNOTATION_PATTERN.match(cs.chordKindStr.lower()),
            f"chord symbol '{cs.chordKindStr}' at offset {cs.offset} is invalid",
        )
        for part, cs in chord_symbols.items()
    }
    UNSPECIFIED = "unspecified"
    # Group into harmonic_rhythms and harmonic_scopes per part
    harmonic_rhythm_css = {
        part: group_or_default(parsed_cs, "harmonic_rhythm", UNSPECIFIED)
        for part, parsed_cs in parsed_chord_symbols.items()
    }
    harmonic_parts_css = {
        part: group_or_default(parsed_cs, "harmonic_parts", UNSPECIFIED)
        for part, parsed_cs in parsed_chord_symbols.items()
    }
    # print(f"{harmonic_rhythm_css=}")
    # print(f"{harmonic_parts_css=}")

    # --------validation--------
    # At most one unique harmonic_rhythm should be specified across all parts
    assert len(set(harmonic_rhythm_css.values())) <= 1
    # At most one unique harmonic_scope should be specified in all parts
    # (either `a` or `p`)
    assert len(set(harmonic_parts_css.values())) <= 1

    # --------filter parts--------
    # If at least one chord_symbol uses a `p`,
    # then restrict to only parts with a chord symbol on them
    harmonic_parts: set[Part]
    if any(hp == "p" for hp in harmonic_parts_css.values()):
        # only specified parts
        harmonic_parts = set(harmonic_parts_css.keys())
    else:
        # `a`, all parts
        harmonic_parts = set(m21_score.parts)

    # --------remove x'd notes--------
    # remove specific NotRest entities on offsets+parts annotated with x

    # filter generator to strip out elements if they're x'd out
    def filter_block_by_x_in_part(part: Part) -> Callable[[Music21Object], bool]:
        if part not in x_symbols_2:
            return lambda _: True
        blocked_offsets = x_symbols_2[part]

        def filter_block_by_x(el: Music21Object) -> bool:
            el_offset = el.getOffsetInHierarchy(part)
            return el_offset not in blocked_offsets

        return filter_block_by_x

    # Filter all the notes in each part by x's annotated in score
    harmonic_elements = {
        part: part.recurse()
        .getElementsByClass(NotRest)
        .getElementsNotOfClass(NoChord)
        .getElementsByOffsetInHierarchy(range[0], range[1], includeEndBoundary=False)
        .addFilter(filter_block_by_x_in_part(part))
        for part in harmonic_parts
    }

    # --------group notes into clusters--------
    # split out beat/measure repeats
    cluster_starts: list[OffsetQL]
    if "n" in harmonic_rhythm_css.values() or all(
        hr == UNSPECIFIED for hr in harmonic_rhythm_css.values()
    ):
        # one long chord block
        cluster_starts = [range[0]]
    elif "m" in harmonic_rhythm_css.values():
        # one chord block per measure
        cluster_starts = get_unique_offsets(
            m21_score.recurse()
            .getElementsByClass(Measure)
            .getElementsByOffset(range[0], range[1]),
            offsetSite=m21_score,
        )
    else:
        # one chord block per offset range
        offset_step = Fraction(next(iter(harmonic_rhythm_css.values())))
        cluster_starts = list(frange(range[0], range[1], offset_step))
    ranges = [
        (
            cluster_start,
            cluster_starts[idx + 1] if idx + 1 < len(cluster_starts) else range[1],
        )
        for idx, cluster_start in enumerate(cluster_starts)
    ]
    # combine `ranges` and `harmonic_elements` into list[list[NotRest]]
    harmonic_clusters: list[tuple[OffsetQL, list[NotRest]]] = []
    for r_start, r_end in ranges:
        # select all NotRest elements in [r_start, r_end) across all parts
        harmonic_clusters.append(
            (
                r_start,
                [
                    el
                    for partNotRests in harmonic_elements.values()
                    for el in set(
                        partNotRests.getElementsByOffsetInHierarchy(
                            r_start, r_end, includeEndBoundary=False
                        )
                    )
                ],
            )
        )

    # resolve into chords
    return [
        (offset, Chord(extract_pitches(cluster)))
        for offset, cluster in harmonic_clusters
    ]


def extract_harmonic_clusters(m21_score: Score) -> list[tuple[OffsetQL, Chord]]:
    """
    Identify harmonic clusters with the help of ChordSymbol / NoChord annotations.
    Rules:
    1.  Default behavior is to group notes across all parts by measure for programmatic harmonic analysis.
        (This is equivalent to a NoChord annotation of `ma`.)
    2.  Any ChordSymbol or NoChord symbol sets the harmonic behavior until the next annotation is given.
    3.  Any ChordSymbol on any part sets the chord to be used, bypassing programmatic analysis.
        Multiple different ChordSymbols for different parts on the same beat is undefined behavior.
    4.  NoChord symbols (i.e. "chord" text that isn't an actual chord) have specific behaviors based on the text written:
        -   x means to ignore all notes on this beat on this part
        -   any other symbol indicates a new chord starts here, and includes two halves (each optional, but needs at least one):
            -   harmonic_rhythm: how long until the next chord?
                `n` means "never", or until the next annotation. (default)
                `(number)` means "repeat every # quarter beats" until another annotation is given.
                `m` means "every measure", i.e. the original default behavior.
            -   harmonic_part_scope: which parts should i include for harmonic analysis?
                `a` means "all parts" (default)
                `p` means "this part (and all others notated on this beat with `p`).
    """
    chord_symbols, x_symbols = extract_chord_symbols(m21_score)
    chords: list[tuple[OffsetQL, Chord]] = []
    for idx, css_at_offset in enumerate(chord_symbols):
        range_start = css_at_offset[0]
        range_end = (
            chord_symbols[idx + 1][0]
            if idx + 1 < len(chord_symbols)
            else m21_score.highestTime
        )
        # TODO: optimization: filter x_symbols to only those in range?
        chords.extend(
            process_chord_annotation(
                m21_score, (range_start, range_end), css_at_offset[1], x_symbols
            )
        )
    return chords


def parse_score_data(data) -> MusicData:
    m21_score = converter.parseData(data)

    if not isinstance(m21_score, Score):
        raise ValueError(
            "Can only render musicxml files containing a Score, not a "
            + type(m21_score)
        )

    music_data = MusicData(m21_score)

    for offset, chord in music_data.chords:
        print(
            f"{offset:5}: {chord.pitchedCommonName:>25} ({' '.join(f"{p.nameWithOctave:3}" for p in sorted(chord.pitches)) if len(chord.pitches) > 0 else "no notes"})"
        )
    for offset, note in music_data.all_notes:
        print(f"{offset:5}: {note.nameWithOctave} {note.duration.quarterLength}")
    for part, notes in music_data.all_notes_by_part.items():
        print(f"{part}")
        for offset, note in notes:
            print(f"\t{offset:5}: {note.nameWithOctave} {note.duration.quarterLength}")

    return music_data
