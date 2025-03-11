# std library
from dataclasses import dataclass

# 3rd party library
from music21 import stream, note, converter

# project files
from utils import get_root_note


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


def parse_score_data(data) -> MusicData:
  m21_score = converter.parseData(data)
  if not isinstance(m21_score, stream.Score):
    raise ValueError("Can only render musicxml files containing a Score, not a " + type(m21_score))

  # print(m21_score)
  # parts = m21_score.getElementsByClass(stream.Part)
  # for x in parts:
  #   print("\t" + str(x))

  return MusicData(m21_score)

