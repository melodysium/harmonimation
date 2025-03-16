# std library
from dataclasses import dataclass

# 3rd party library
from music21 import stream, note, chord, harmony, converter

# project files
from utils import get_root_note, print_notes_stream, display_timing, extract_notes, display_chord, display_notRest, copy_timing, timing_from, Music21Timing, find_direct_owner, find_owner, group_by_offset, display_id, find_direct_owner_tree


# data transfer class
@dataclass
class MusicData:
  chord_roots: stream.Stream[note.Note] # TODO: change to chord_blocks that groups all notes per harmonic section together
  all_notes: stream.Stream[note.Note]
  all_notes_by_part: object = None # TODO: what would this look like?
  bpm: object = None # TODO: what would this look like?
  current_key: object = None # TODO: what would this look like?
  lyrics: object = None # TODO: what would this look like?
  comments: object = None # TODO: what would this look like?

  def __init__(self, m21_score: stream.Score):
    self.all_notes = extract_individual_notes(m21_score)
    self.chord_roots = extract_chord_roots(m21_score)


def extract_individual_notes(m21_score: stream.Score) -> stream.Stream[note.Note]:
  single_notes = m21_score.recurse().getElementsByClass(note.Note).stream()
  m21_note: note.Note
  # print_notes_stream(single_notes)
  chord_notes = stream.Stream()
  for m21_chord in stream.Stream(m21_score.flatten().getElementsByClass(chord.Chord)):
    m21_notes = m21_chord.notes
    for m21_note in m21_notes:
      chord_notes.insert(m21_chord.offset, m21_note)
  # print_notes_stream(chord_notes)
  # zip streams together
  all_notes = stream.Stream()
  all_notes.insert(0, single_notes)
  all_notes.insert(0, chord_notes)
  all_notes = all_notes.flatten()
  # print_notes_stream(all_notes)
  return all_notes


def extract_chord_roots(m21_score: stream.Score) -> stream.Stream[note.Note]:
  chords = m21_score.chordify().flatten().getElementsByClass(chord.Chord).stream()
  # print_chords_stream(chords)
  chord_roots = stream.Stream(list(map(get_root_note, chords)))
  # print_notes_stream(chord_roots)
  return chord_roots


def extract_chord_symbols(m21_score: stream.Score) -> list[tuple[float, dict[stream.Part, harmony.ChordSymbol]]]:
  flattened_score = m21_score.flatten()
  all_chord_symbols: stream.Stream[harmony.ChordSymbol] = flattened_score.getElementsByClass(harmony.ChordSymbol)#.stream()
  print(len(all_chord_symbols))

  # assemble the list by looking at all chord symbols at each unique offset
  grouped_chord_symbols: list[tuple[float, dict[stream.Part, harmony.ChordSymbol]]] = []
  for chord_symbol_group in group_by_offset(all_chord_symbols):
    offset = chord_symbol_group.offset
    # print(len(chord_symbol_group))
    # for cs in chord_symbol_group:
    #     print(f"{cs.id=}, owner={find_owner(cs, m21_score.parts, error_if_not_found=True)}, direct_owner={find_direct_owner(cs, m21_score).id}")
    #     print(f"{" -> ".join([display_id(x) for x in find_direct_owner_tree(cs, m21_score)])}")
    part_dict = {find_owner(cs, m21_score.parts, error_if_not_found=True): cs for cs in chord_symbol_group}
    grouped_chord_symbols.append((offset, part_dict))
  return grouped_chord_symbols


def analyze_harmonic_cluster(notes: stream.Stream[note.Note]) -> chord.Chord:
  return copy_timing(chord.Chord(notes), timing_from(notes))


def extract_harmonic_clusters(m21_score: stream.Score) -> stream.Stream[chord.Chord]:
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
      -   any other symbol indicates a new chord starts here, and is parsed as ([0-9]*|m|n)?(p|a)?:
          -   first half means "how long until the next chord?"
              `n` means "never", or until the next annotation. (default)
              `(number)` means "repeat every # quarter beats" until another annotation is given.
              `m` means "every measure", i.e. the original default behavior.
          -   second half means "which parts should i include for analysis?"
              `a` means "all parts" (default)
              `p` means "this part (and all others notated on this beat with `p`).
  """
  chord_symbols = extract_chord_symbols(m21_score)
  for cs in chord_symbols:
    print(cs)
  # TODO: implement harmonic grouping logic described above

  # default behavior - group by all parts by measure
  # first_4_measure = m21_score.getElementsByOffset(0, 12, includeEndBoundary=False).stream()
  # for elem in first_4_measure.recurse():
  #   print(f"{display_timing(elem)}: {elem}")

  m21_chords: list[chord.Chord] = []

  m21_all_measures: stream.Stream[stream.Measure] = m21_score.recurse().getElementsByClass(stream.Measure).stream()
  # print(len(m21_all_measures))
  measure_start_offsets = sorted(set([m.offset for m in m21_all_measures]))
  # print(measure_start_offsets)
  # measure: stream.Measure
  # for measure in m21_all_measures:
  #   print(f"{display_timing(measure)}: {measure.number}")
  for measure_offset in measure_start_offsets:
    # get all measures at this offset
    part_measures: stream.Stream[stream.Measure] = m21_all_measures.getElementsByOffset(measure_offset, measure_offset).stream()
    measure_timing = Music21Timing(measure_offset, part_measures.first().duration)
    copy_timing(part_measures, measure_timing)
    # print(f"{display_timing(part_measures)} (measure {measure_offset:>5}): {len(part_measures)} Measures")

    # get all notes and chords during these measures
    not_rest_elems: stream.Stream[note.NotRest] = copy_timing(part_measures.recurse().getElementsByClass(note.NotRest).stream(), measure_timing)
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
  return stream.Stream(m21_chords)


def parse_score_data(data) -> MusicData:
  m21_score = converter.parseData(data)
  if not isinstance(m21_score, stream.Score):
    raise ValueError("Can only render musicxml files containing a Score, not a " + type(m21_score))

  # print(m21_score)
  # parts = m21_score.getElementsByClass(stream.Part)
  # for x in parts:
  #   # print("\t" + str(x))
  clusters = extract_harmonic_clusters(m21_score)
  # TODO: finish implementing harmonic_clusters behavior
  # import sys; sys.exit(0)

  return MusicData(m21_score)

