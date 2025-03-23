# std library
from dataclasses import dataclass
from fractions import Fraction

# 3rd party library
from music21 import converter
from music21.chord import Chord
from music21.common.types import OffsetQL
from music21.harmony import ChordSymbol, NoChord
from music21.note import Note, NotRest
from music21.stream import Stream, Score, Part, Measure
from music21.stream.filters import IsFilter, IsNotFilter, ClassNotFilter
import regex as re # stdlib re doesn't support multiple named capture groups with the same name, i use it below

# project files
from utils import get_root_note, extract_notes, copy_timing, timing_from, Music21Timing, get_unique_offsets, assert_not_none, group_or_default, frange
from utils import group_by_offset, print_notes_stream, display_timing, display_chord, display_notRest, display_id


DEFAULT_CHORD_SYMBOL = ChordSymbol(kindStr="ma")
# TODO: replace 


# data transfer class
@dataclass
class MusicData:
  chord_roots: Stream[Note] # TODO: change to chord_blocks that groups all notes per harmonic section together
  all_notes: Stream[Note]
  all_notes_by_part: object = None # TODO: what would this look like?
  bpm: object = None # TODO: what would this look like?
  current_key: object = None # TODO: what would this look like?
  lyrics: object = None # TODO: what would this look like?
  comments: object = None # TODO: what would this look like?

  def __init__(self, m21_score: Score):
    self.all_notes = extract_individual_notes(m21_score)
    self.chord_roots = extract_chord_roots(m21_score)


def extract_individual_notes(m21_score: Score) -> Stream[Note]:
  single_notes = m21_score.recurse().getElementsByClass(Note).stream()
  m21_note: Note
  # print_notes_stream(single_notes)
  chord_notes = Stream()
  for m21_chord in Stream(m21_score.flatten().getElementsByClass(Chord)):
    m21_notes = m21_chord.notes
    for m21_note in m21_notes:
      chord_notes.insert(m21_chord.offset, m21_note)
  # print_notes_stream(chord_notes)
  # zip streams together
  all_notes = Stream()
  all_notes.insert(0, single_notes)
  all_notes.insert(0, chord_notes)
  all_notes = all_notes.flatten()
  # print_notes_stream(all_notes)
  return all_notes


def extract_chord_roots(m21_score: Score) -> Stream[Note]:
  chords = m21_score.chordify().flatten().getElementsByClass(Chord).stream()
  # print_chords_stream(chords)
  chord_roots = Stream(list(map(get_root_note, chords)))
  # print_notes_stream(chord_roots)
  return chord_roots


def extract_chord_symbols(m21_score: Score)\
  -> tuple[
      # list[tuple[offset, ...]]
      list[tuple[OffsetQL,
                 # non-`x` chord symbol per part at this offset
                 dict[Part, ChordSymbol]]],
      list[tuple[OffsetQL,
                 # parts at this offset with an `x`
                 set[Part]]]
  ]:
  # get each chord symbol, paired with its part
  chord_symbols_by_part = sorted(
      [
        (part, chord_symbol)
        for part in m21_score.parts
        for chord_symbol in part.recurse().getElementsByClass(ChordSymbol)
      ],
      key=lambda t: t[1].getOffsetInHierarchy(t[0]))

  # identify all non-`x` chord symbols
  harmonic_span_chord_symbols_by_part = list(filter(
      lambda t: t[1].chordKindStr.lower() != "x",
      chord_symbols_by_part))
  # get a list of all unique offsets
  unique_offsets = get_unique_offsets(
      [t[1] for t in harmonic_span_chord_symbols_by_part],
      offsetSite=m21_score)
  # for each unique offset, grab all the chord symbols at that offset,
  # and make a dict from part to chord symbol
  chord_symbols_per_part_per_offset = [
      (
        offset,
        {
          t[0]: t[1]
          for t in harmonic_span_chord_symbols_by_part
          if t[1].getOffsetInHierarchy(m21_score) == offset
        }
      )
      for offset in unique_offsets]
  # if no chord symbol in first measure, insert a default one
  if chord_symbols_per_part_per_offset[0][0] > 0:
    chord_symbols_per_part_per_offset.insert(
        0,
        (0.0, {m21_score.parts.first(): DEFAULT_CHORD_SYMBOL}))

  # identify all the `x` chord symbols
  x_chord_symbols_by_part = list(filter(
      lambda t: t[1].chordKindStr.lower() == "x",
      chord_symbols_by_part))
  # get a list of all unique offsets
  x_unique_offsets = get_unique_offsets(
      [t[1] for t in x_chord_symbols_by_part],
      offsetSite=m21_score)
  # for each unique offset, make a set of all Parts with an x at that offset
  parts_with_x_per_offset = [
      (
        offset,
        {
          t[0]
          for t in x_chord_symbols_by_part
          if t[1].getOffsetInHierarchy(m21_score) == offset
        }
      )
      for offset in x_unique_offsets]

  return (chord_symbols_per_part_per_offset, parts_with_x_per_offset)


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
    # "x",
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
    x_symbols: list[tuple[OffsetQL, set[Part]]]
  ) -> list[Chord]:

  # Easy case: Chord is hard-coded
  if len([cs for cs in chord_symbols.values() if not isinstance(cs, NoChord)]):
    # Validation: If manual chord is set, it should be alone
    if len(chord_symbols) > 1:
      raise ValueError("Invalid annotation - cannot have manual chord set in the same beat as any other chord annotations.")
    return next(chord_symbols.values())
  
  # Complicated case: Parse the NoChords
  # --------parsing--------
  parsed_chord_symbols = {
    part: assert_not_none(
      CHORD_ANNOTATION_PATTERN.match(cs.chordKindStr.lower()),
      f"chord symbol '{cs.chordKindStr}' at offset {cs.offset} is invalid")
    for part, cs in chord_symbols.items()}
  UNSPECIFIED = "unspecified"
  # Group into harmonic_rhythms and harmonic_scopes per part
  harmonic_rhythm_css = {part: group_or_default(parsed_cs, "harmonic_rhythm", UNSPECIFIED) for part, parsed_cs in parsed_chord_symbols.items()}
  harmonic_parts_css = {part: group_or_default(parsed_cs, "harmonic_parts", UNSPECIFIED) for part, parsed_cs in parsed_chord_symbols.items()}
  print(f"{harmonic_rhythm_css=}")
  print(f"{harmonic_parts_css=}")

  # --------validation--------
  # At most one unique harmonic_rhythm should be specified across all parts
  assert len(set(harmonic_rhythm_css.values())) <= 1
  # At most one unique harmonic_scope should be specified in all parts (either `a` or `p`)
  assert len(set(harmonic_parts_css.values())) <= 1

  # --------filter parts--------
  # If at least one chord_symbol uses a `p`, then restrict to only parts with a chord symbol on them
  harmonic_parts: Stream[Part]
  if any(hp == 'p' for hp in harmonic_parts_css.values()):
    # only specified parts
    harmonic_parts = m21_score.parts.addFilter(IsFilter(list(harmonic_parts_css.keys()))).stream()
  else:
    # `a`, all parts
    harmonic_parts = m21_score.parts.stream()
  # TODO: this following line is the one that breaks the getContextByClass() calls
  # TODO: maybe print contextSites() before and after to see what changed?
  harmonic_parts.recurse().getElementsByClass(Measure).first().getContextByClass(Part)
  scoped_measures: Stream[Measure] = harmonic_parts.recurse().getElementsByClass(Measure).stream()
  print(len(scoped_measures))
  scoped_measures.recurse().getElementsByClass(Measure).first()

  print(scoped_measures.first().getContextByClass(Part))
  print("")
  for m in scoped_measures:
    m.activeSite = m21_score
    
    print(f"measure\n{display_timing(m)}: {m} {m.groups} {m.getContextByClass(Part)}")
    for e in m.getElementsByClass(NotRest).addFilter(ClassNotFilter(ChordSymbol)).stream():
      n: NotRest = e
      print(f"\t{display_notRest(n)} {n.groups} {n.getContextByClass(Part)} \n\t\t{'\n\t\t'.join([str(x) for x in n.contextSites()])}")
    print()
  print(m21_score.containerInHierarchy(scoped_measures[0]) in m21_score.parts[0])

  # --------remove x'd notes--------
  # remove specific NotRest entities on offsets+parts annotated with x
  # first get list of all offsets+parts wtih 


  # --------group notes into clusters--------
  # split out beat/measure repeats
  cluster_starts: list[OffsetQL]
  if 'n' in harmonic_rhythm_css.values() or all(hr == UNSPECIFIED for hr in harmonic_rhythm_css.values()):
    # one long chord block
    cluster_starts = [range[0]]
  elif 'm' in harmonic_rhythm_css.values():
    # one chord block per measure
    cluster_starts = get_unique_offsets(scoped_measures)
  else:
    # one chord block per offset range
    offset_step = Fraction(next(iter(harmonic_rhythm_css.values())))
    cluster_starts = list(frange(range[0], range[1], offset_step))
  ranges = [(
      cluster_start,
      cluster_starts[idx+1] if idx+1 < len(cluster_starts) else range[1],
    ) for idx, cluster_start in enumerate(cluster_starts)]

  # TODO: use extract_notes and analyze_harmonic_cluster to determine chords


def extract_harmonic_clusters(m21_score: Score) -> Stream[Chord]:
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
  for cs in chord_symbols:
    print(cs)
  print(x_symbols)
  # import sys; sys.exit(0)
  chords: list[Chord] = []
  for idx, css_at_offset in enumerate(chord_symbols):
    print(css_at_offset)
    range_start = css_at_offset[0]
    range_end = chord_symbols[idx+1][0] if idx+1 < len(chord_symbols) else m21_score.highestTime
    x_symbols_during_range = filter(lambda t: t[0] >= range_start and t[0] < range_end, x_symbols)
    chords.extend(process_chord_annotation(m21_score, (range_start, range_end), css_at_offset[1], x_symbols_during_range))
  # TODO: return chords!

  # default behavior - group by all parts by measure
  # first_4_measure = m21_score.getElementsByOffset(0, 12, includeEndBoundary=False).stream()
  # for elem in first_4_measure.recurse():
  #   print(f"{display_timing(elem)}: {elem}")

  m21_chords: list[Chord] = []

  m21_all_measures: Stream[Measure] = m21_score.recurse().getElementsByClass(Measure).stream()
  # print(len(m21_all_measures))
  measure_start_offsets = sorted(set([m.offset for m in m21_all_measures]))
  # print(measure_start_offsets)
  # measure: Measure
  # for measure in m21_all_measures:
  #   print(f"{display_timing(measure)}: {measure.number}")
  for measure_offset in measure_start_offsets:
    # TODO: rework to use getOffsetBySite()
    # get all measures at this offset
    part_measures: Stream[Measure] = m21_all_measures.getElementsByOffset(measure_offset, measure_offset).stream()
    measure_timing = Music21Timing(measure_offset, part_measures.first().duration)
    copy_timing(part_measures, measure_timing)
    # print(f"{display_timing(part_measures)} (measure {measure_offset:>5}): {len(part_measures)} Measures")

    # get all notes and chords during these measures
    not_rest_elems: Stream[NotRest] = copy_timing(part_measures.recurse().getElementsByClass(NotRest).stream(), measure_timing)
    # print(f"{display_timing(not_rest_elems)}: {len(not_rest_elems)} NotRests")
    # for elem in not_rest_elems:
    #   print(display_notRest(elem))

    # get all individual notes
    notes = copy_timing(extract_notes(not_rest_elems), measure_timing)
    # print(f"{display_timing(notes)}: {len(notes)} Notes")
    # print_notes_stream(notes, all_elements=True)

    # combine all notes into one chord
    m21_chord = analyze_harmonic_cluster(notes)
    # print(display_chord(m21_chord))
    m21_chords.append(m21_chord)
    # print()
  return Stream(m21_chords)


def parse_score_data(data) -> MusicData:
  m21_score = converter.parseData(data)

  if not isinstance(m21_score, Score):
    raise ValueError("Can only render musicxml files containing a Score, not a " + type(m21_score))

  # print(m21_score)
  # parts = m21_score.getElementsByClass(Part)
  # for x in parts:
  #   # print("\t" + str(x))
  clusters = extract_harmonic_clusters(m21_score)
  # TODO: finish implementing harmonic_clusters behavior
  import sys; sys.exit(0)

  return MusicData(m21_score)

