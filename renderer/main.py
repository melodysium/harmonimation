
# standard lib
import argparse

# 3rd party
from music21 import *
from manim import *

# project files
from scene_glasspanel import GlassPanel

# --------------------HELPERS--------------------

def parse_args():
  parser = argparse.ArgumentParser(
                    prog='Harmonimation',
                    description='A program for visualizing musical harmonic analysis',
                    epilog='Created by melodysium')
  parser.add_argument('filename', type=argparse.FileType(), help="musicxml file to render")
  return parser.parse_args()

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

def get_root_note(m21_chord: chord.Chord) -> note.Note:
  m21_note = note.Note(m21_chord.root())
  m21_note.duration = m21_chord.duration
  m21_note.offset = m21_chord.offset
  return m21_note

# --------------------MAIN CONRTOL FLOW--------------------

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


def parse_score_data(data) -> stream.Score:
  m21_score = converter.parseData(data)
  if not isinstance(m21_score, stream.Score):
    raise ValueError("Can only render musicxml files containing a Score, not a " + type(m21_score))
  return m21_score
    

def main():

  args = parse_args()
  m21_score = parse_score_data(args.filename.read())
  
  # hack for now - ignore timing, hard-code BPM
  bpm = 180

  print(m21_score)
  parts = m21_score.getElementsByClass(stream.Part)
  for x in parts:
    print("\t" + str(x))

  # get all individual notes
  print("All individual notes")
  all_notes = extract_individual_notes(m21_score)

  # get chord roots
  print("Calculating chord roots")
  chord_roots = extract_chord_roots(m21_score)

  return


  # get left hand separate from right hand
  melody_partstaff = m21_score[4]
  melody_flat = stream.Stream(melody_partstaff.flatten().getElementsByClass(note.GeneralNote))
  chords_partstaff = m21_score[5]
  chords_flat = stream.Stream(chords_partstaff.flatten().getElementsByClass(note.GeneralNote))
  for i in range(20):
    e = chords_flat[i]
    if isinstance(e, m21_chord_rootnote.Chord):
      print(display_chord(e))
  
  print(melody_partstaff.highestTime) # 160
  print(melody_partstaff.highestTime) # 160

  melody_flat.show('text')
  # chords_flat.show('text')

  # panel = GlassPanel()
  # panel.render()

from obj_music_circles import Circle12NotesSequenceConnectors, PlayCircle12Notes
# from obj_music_circles import Circle12NotesBase, PlayCircle12NotesV2
# TODO: add non-root "highlights" around other notes being played

# TODO: make textboxes with programmed text throughout the piece

class testPlayFromMusicXML(Scene):
  def construct(self):

    import os
    print(os.getcwd())

    with open("../test_scores/My Time - 6m loop section.musicxml") as f:
      m21_score = parse_score_data(f.read())
    
    
  
    # hack for now - ignore timing, hard-code BPM
    bpm = 180

    print(m21_score)
    parts = m21_score.getElementsByClass(stream.Part)
    for x in parts:
      print("\t" + str(x))

    # get all individual notes
    print("All individual notes")
    all_notes = extract_individual_notes(m21_score)
    print(f"{len(all_notes)} notes")

    # get chord roots
    print("Calculating chord roots")
    chord_roots = extract_chord_roots(m21_score)
    print(f"{len(chord_roots)} chord roots")


    self.wait(0.2)
    title_text = Text("Interval Cycle (-1, +5)", font_size=36).shift(3.1 * UP)
    subtitle_text = Text("from bo en - My Time", font_size=24).shift(2.5 * UP)
    circle_chromatic = Circle12NotesSequenceConnectors(radius=1.5, max_selected_steps=6).shift(2 * LEFT + 0.5 * DOWN)
    text_chromatic = Text("Chromatic circle", font_size=24).move_to(circle_chromatic).shift(2 * DOWN)
    circle_fifths = Circle12NotesSequenceConnectors(radius=1.5, max_selected_steps=6, note_intervals=7).shift(2 * RIGHT + 0.5 * DOWN)
    text_fifths = Text("Circle of Fifths", font_size=24).move_to(circle_fifths).shift(2 * DOWN)
    self.play(
      Create(title_text),
      Create(subtitle_text),
      circle_chromatic.create(),
      Create(text_chromatic),
      circle_fifths.create(),
      Create(text_fifths),
      run_time=2)
    self.wait(1)

    play_circle_chromatic = PlayCircle12Notes(bpm=bpm, notes=chord_roots, circle12=circle_chromatic)
    play_circle_fifths = PlayCircle12Notes(bpm=bpm, notes=chord_roots, circle12=circle_fifths)
    self.play(AnimationGroup(
      play_circle_chromatic,
      play_circle_fifths,
      ))


if __name__ == '__main__':
  main()