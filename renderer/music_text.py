from music.music_constants import Note
from manim import Tex, Text, Scene, LEFT, RIGHT, Create, TexTemplate
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
    def __init__(self, note: Note, **kwargs):
      Text.__init__(self, note.display_portable, **kwargs)
      self.note = note
else:
  class TextNote(Tex):
    def __init__(self, note: Note, **kwargs):
      Tex.__init__(self, note.display, tex_template=myTemplate, **kwargs)
      self.note = note


class test(Scene):
  def construct(self):
    self.wait(0.2)
    note_C = TextNote(Note.C)
    note_Cb = TextNote(Note.Cb).shift(2 * LEFT)
    note_Cs = TextNote(Note.Cs).shift(2 * RIGHT)
    self.play(Create(note_Cb), Create(note_C), Create(note_Cs), run_time=2)
    self.wait(1)