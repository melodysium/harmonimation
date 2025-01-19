
# standard lib
import argparse

# 3rd party
from music21 import *
# from manim import 

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

# --------------------MAIN CONRTOL FLOW--------------------

def main():

  args = parse_args()

  score = converter.parseData(args.filename.read())
  if not isinstance(score, stream.Score):
    raise ValueError("Can only render musicxml files containing a Score, not a " + type(score))
  
  # hack for now - ignore timing, hard-code BPM
  bpm = 128
  # get left hand separate from right hand
  melody = score[1]
  melody_flat = stream.Stream(melody.flatten().getElementsByClass(note.GeneralNote))
  chords = score[2]
  chords_flat = stream.Stream(chords.flatten().getElementsByClass(note.GeneralNote))
  for i in range(20):
    e = chords_flat[i]
    if isinstance(e, chord.Chord):
      print(f"{e.offset:5} {e.root().name} {e.quality} {e.fullName}")
  
  # print(melody.highestTime) # 160
  # print(chords.highestTime) # 160

  # melody_flat.show('text')
  # chords_flat.show('text')

  # panel = GlassPanel()
  # panel.render()
  


if __name__ == '__main__':
  main()