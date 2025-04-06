from dataclasses import dataclass
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
\usepackage{xcolor}
\newunicodechar{𝄫}{\musDoubleFlat}
\newunicodechar{♭}{\musFlat}
\newunicodechar{♮}{\musNatural}
\newunicodechar{♯}{\musSharp}
\newunicodechar{𝄪}{\musDoubleSharp}"""
)

print(f"{USE_LATEX=}")
if USE_LATEX:

    class MusicText(Tex):

        _original_font_size: float

        def __init__(
            self,
            *args,
            font_size: float = DEFAULT_FONT_SIZE,
            **kwargs,
        ):
            # apparently when rendering in Tex the font size is much smaller compared to a Text object,
            # so we'll artificially bump it up here
            self._original_font_size = font_size
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


class ChordText(MusicText):

    def play(
        self,
        music_data: MusicData,
        color: ManimColor = None,  # Leaving as `None` will keep same color as initial
        font_size: int = None,  # Leaving as `None` will keep same font_size as initial
    ) -> Animation:
        return PlayMusicText(
            music_data.bpm,
            [
                MusicTextState(offset, display_chord_short(chord), color, font_size)
                for offset, chord in music_data.chords
            ],
            music_text=self,
        )


class LyricText(MusicText):

    def play(
        self,
        music_data: MusicData,
        color: ManimColor = None,  # Leaving as `None` will keep same color as initial
        font_size: int = None,  # Leaving as `None` will keep same font_size as initial
    ) -> Animation:
        # TODO: would be cool if new lyrics swept in from the right side while bumping out old lyrics to the left, instead
        text_steps: list[tuple[OffsetQL, str]] = []
        # loop through all lyrics in the song
        for _, syllables in music_data.lyrics:
            # make a unique animation step for each syllable in each lyric
            for cur_syl_offset, cur_syl_text in syllables:
                # make a LaTeX text with the current syllable emphasized
                # TODO: i might want to use a partially obscured underline, like this one:
                # https://tex.stackexchange.com/questions/528798/underlining-text-in-latex-no-vertical-gap
                # or possibly a dot way below the text?
                syllable_emphasized_text = "-".join(
                    (
                        r"\underline{" + syl_text + r"}"
                        if syl_text is cur_syl_text and len(syllables) > 1
                        else syl_text
                    )
                    for _, syl_text in syllables
                )
                # add all of this into a MusicTextState
                text_steps.append(
                    MusicTextState(
                        cur_syl_offset,
                        syllable_emphasized_text,
                        color,
                        font_size,
                    )
                )
        return PlayMusicText(
            music_data.bpm,
            text_steps,
            music_text=self,
        )


class NoteText(MusicText):
    def __init__(self, note: Note, omit_natural: bool = True, **kwargs):
        MusicText.__init__(
            self,
            note.display(use_unicode_symbols=USE_LATEX, omit_natural=omit_natural),
            **kwargs,
        )
        self.note = note


@dataclass
class MusicTextState:
    offset: OffsetQL
    text: str
    color: ManimColor | None = None  # None means "keep previous"
    font_size: float | None = None  # None means "keep previous"


class PlayMusicText(Succession):

    VERY_SMALL = 2**-32

    def __init__(
        self,
        bpm: float,
        text: list[MusicTextState],
        music_text: MusicText,  # NOTE: must be a dummy object with the desired position and SOME POINTS, even if they're transparent
        transition_time: float = 0.1,  # in seconds
        **kwargs,
    ):
        bps = bpm / 60
        # TODO: figure out how to set frame-0 text if in offset 0 from `text` param
        # TODO: figure out how to specify position / color / etc if not passing a template object in
        # TODO: left alignment?

        anims: list[Animation] = []
        previous_offset = 0
        previous_color = music_text.color
        previous_font_size = music_text._original_font_size

        def get_new_obj(val: MusicTextState) -> MusicText:
            nonlocal previous_color, previous_font_size
            ob = MusicText(val.text).move_to(music_text)
            ob.color = previous_color = val.color or previous_color
            ob.font_size = previous_font_size = val.font_size or previous_font_size
            return ob

        for text_state in text:
            # special case - allow first offset of 0 even though previous_offset = 0
            if text_state.offset == 0:
                anims.append(
                    Transform(
                        music_text,
                        get_new_obj(text_state),
                        run_time=PlayMusicText.VERY_SMALL,
                    )
                )
                previous_offset = PlayMusicText.VERY_SMALL
                continue

            assert text_state.offset > previous_offset

            # create animation for this latest text value
            anim = Transform(music_text, get_new_obj(text_state))

            # figure out how long since last update
            elapsed_time = (text_state.offset - previous_offset) / bps
            # if we don't have time to do a full wait-then-transition
            if elapsed_time <= transition_time:
                # just transform with the time we have
                anim.run_time = elapsed_time
                anims.append(anim)
            else:
                # sleep until start of time when we need to transform
                anims.append(Wait(elapsed_time - transition_time))
                anim.run_time = transition_time
                anims.append(anim)
            # done processing this offset
            previous_offset = text_state.offset

        super().__init__(anims, **kwargs)


class test(Scene):
    def construct(self):
        self.wait(0.2)
        note_C = NoteText(Note.C)
        note_Cb = NoteText(Note.Cb).shift(2 * LEFT)
        note_Cs = NoteText(Note.Cs).shift(2 * RIGHT)
        self.play(Create(note_Cb), Create(note_C), Create(note_Cs), run_time=2)
        self.wait(1)


class testPlayMusicalText(Scene):
    def construct(self):
        self.wait(0.2)

        music_text = MusicText(".asdfasfasf", color=ManimColor([1, 1, 1, 0])).move_to(
            UP * 1 + RIGHT * 1
        )
        print(music_text.get_center())
        # music_text2 = MusicalText("").move_to(UP * -1 + RIGHT * -1)
        # print(music_text2.get_center())
        # print(music_text2.points)
        # self.play(Create(music_text))
        self.add(music_text)
        self.wait(1)

        updates = [(i, f"Beat {i}") for i in range(50)]
        self.play(PlayMusicText(180, updates, music_text, transition_time=5))
        self.wait(1)
