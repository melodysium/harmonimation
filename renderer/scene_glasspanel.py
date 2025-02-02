

# standard libs


# 3rd party libs
from manim import *

# project files
from obj_music_circles import Circle12NotesSequenceConnectors
from obj_rhythm_circle import CircleRhythm
from obj_music_text import TextNote



class GlassPanel(Scene):

  # def __init__(self):
  #   pass

  def construct(self):
    
    self.wait(0.2)
    
    # manually create gadgets
    circle_rhythm = CircleRhythm(radius=1.2).shift(3 * RIGHT + 2 * DOWN)
    circle_chromatic = Circle12NotesSequenceConnectors(radius=1.2).shift(3 * RIGHT + 2 * UP)
    circle_fifths = Circle12NotesSequenceConnectors(radius=1.2, note_intervals=7).shift(3 * LEFT + 2 * UP)
    
    self.play(circle_chromatic.create(), circle_fifths.create(), circle_rhythm.create(), run_time=2)
    self.wait(1)

    