from manim import Tex, Text, Scene, LEFT, RIGHT, Create, TexTemplate

from music.music_constants import Note
from constants import SKIP_LATEX

myTemplate = TexTemplate()
myTemplate.add_to_preamble(r"""\usepackage{musicography} 
\usepackage{newunicodechar}
\newunicodechar{𝄫}{\musDoubleFlat} 
\newunicodechar{♭}{\musFlat} 
\newunicodechar{♮}{\musNatural} 
\newunicodechar{♯}{\musSharp} 
\newunicodechar{𝄪}{\musDoubleSharp}""")

print(f"{SKIP_LATEX=}")
if SKIP_LATEX:
  class TextNote(Text):
    def __init__(self, note: Note, omit_natural: bool=True, **kwargs):
      Text.__init__(self, note.display(rich=False, omit_natural=omit_natural), **kwargs)
      self.note = note
else:
  class TextNote(Tex):
    def __init__(self, note: Note, omit_natural: bool=True, **kwargs):
      Tex.__init__(self, note.display(rich=True, omit_natural=omit_natural), tex_template=myTemplate, **kwargs)
      self.note = note


class test(Scene):
  def construct(self):
    self.wait(0.2)
    note_C = TextNote(Note.C)
    note_Cb = TextNote(Note.Cb).shift(2 * LEFT)
    note_Cs = TextNote(Note.Cs).shift(2 * RIGHT)
    self.play(Create(note_Cb), Create(note_C), Create(note_Cs), run_time=2)
    self.wait(1)