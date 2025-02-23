from manim import Tex, Text, Scene, LEFT, RIGHT, Create, TexTemplate, DEFAULT_FONT_SIZE

from music.music_constants import Note
from constants import USE_LATEX

myTemplate = TexTemplate()
myTemplate.add_to_preamble(r"""\usepackage{musicography} 
\usepackage{newunicodechar}
\newunicodechar{𝄫}{\musDoubleFlat} 
\newunicodechar{♭}{\musFlat} 
\newunicodechar{♮}{\musNatural} 
\newunicodechar{♯}{\musSharp} 
\newunicodechar{𝄪}{\musDoubleSharp}""")

print(f"{USE_LATEX=}")
if USE_LATEX:
  class TextNote(Tex):
    def __init__(self, note: Note, font_size: float=DEFAULT_FONT_SIZE, omit_natural: bool=True, **kwargs):
      # apparently when rendering in Tex the font size is much smaller compared to a Text object,
      # so we'll artificially bump it up here
      font_size = font_size * 1.5
      Tex.__init__(self, note.display(use_unicode_symbols=True, omit_natural=omit_natural), tex_template=myTemplate, font_size=font_size, **kwargs)
      self.note = note
else:
  class TextNote(Text):
    def __init__(self, note: Note, omit_natural: bool=True, **kwargs):
      Text.__init__(self, note.display(use_unicode_symbols=False, omit_natural=omit_natural), **kwargs)
      self.note = note


class test(Scene):
  def construct(self):
    self.wait(0.2)
    note_C = TextNote(Note.C)
    note_Cb = TextNote(Note.Cb).shift(2 * LEFT)
    note_Cs = TextNote(Note.Cs).shift(2 * RIGHT)
    self.play(Create(note_Cb), Create(note_C), Create(note_Cs), run_time=2)
    self.wait(1)
