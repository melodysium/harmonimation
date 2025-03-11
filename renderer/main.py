
# standard lib
import argparse
from dataclasses import dataclass

# 3rd party
import pyjson5

# project files
from scene_glasspanel import GlassPanel
from layout_config import build_widgets
from musicxml import parse_score_data

# --------------------MAIN CONRTOL FLOW--------------------

def parse_args():
  parser = argparse.ArgumentParser(
                    prog='Harmonimation',
                    description='A program for visualizing musical harmonic analysis',
                    epilog='Created by melodysium')
  parser.add_argument('musicxml_file', type=argparse.FileType(), help="musicxml file to render music from")
  parser.add_argument('harmonimation_file', type=argparse.FileType(), help="harmonimation.json file to configure layout")
  return parser.parse_args()


def main():
  # parse program arguments
  args = parse_args()

  # parse music data
  music_data = parse_score_data(args.musicxml_file.read())

  # make harmonimation widgets
  widgets = build_widgets(pyjson5.load(args.harmonimation_file))

  # make harmonimation scene, and render!
  GlassPanel(music_data, widgets).render()


if __name__ == '__main__':
  main()