from typing import TypeVar
from manim import (
    Tex,
    Text,
    Scene,
    LEFT,
    RIGHT,
    UP,
    DOWN,
    Create,
    TexTemplate,
    DEFAULT_FONT_SIZE,
    Animation,
    Succession,
    Wait,
    Transform,
    ManimColor,
)
from music21.common.types import OffsetQL

from music.music_constants import Note
from constants import USE_LATEX
from musicxml import MusicData
from utils import display_chord_short

myTemplate = TexTemplate()
myTemplate.add_to_preamble(
    r"""\usepackage{musicography} 
\usepackage{newunicodechar}
\newunicodechar{𝄫}{\musDoubleFlat} 
\newunicodechar{♭}{\musFlat} 
\newunicodechar{♮}{\musNatural} 
\newunicodechar{♯}{\musSharp} 
\newunicodechar{𝄪}{\musDoubleSharp}"""
)

print(f"{USE_LATEX=}")
if USE_LATEX:

    class MusicText(Tex):
        def __init__(
            self,
            *args,
            font_size: float = DEFAULT_FONT_SIZE,
            **kwargs,
        ):
            # apparently when rendering in Tex the font size is much smaller compared to a Text object,
            # so we'll artificially bump it up here
            font_size = font_size * 1.5
            Tex.__init__(
                self,
                *args,
                tex_template=myTemplate,
                font_size=font_size,
                **kwargs,
            )

else:

    class MusicText(Text): ...


class NoteText(MusicText):
    def __init__(self, note: Note, omit_natural: bool = True, **kwargs):
        MusicText.__init__(
            self,
            note.display(use_unicode_symbols=USE_LATEX, omit_natural=omit_natural),
            **kwargs,
        )
        self.note = note




# TODO: make textboxes with programmed text throughout the piece


class test(Scene):
    def construct(self):
        self.wait(0.2)
        note_C = NoteText(Note.C)
        note_Cb = NoteText(Note.Cb).shift(2 * LEFT)
        note_Cs = NoteText(Note.Cs).shift(2 * RIGHT)
        self.play(Create(note_Cb), Create(note_C), Create(note_Cs), run_time=2)
        self.wait(1)
