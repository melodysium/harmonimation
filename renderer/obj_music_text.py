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
    WHITE,
    VGroup,
)
from music21.common.types import OffsetQL

from music.music_constants import Note
from constants import USE_LATEX
from musicxml import MusicData, MusicDataTiming
from utils import TimestampedAnimationSuccession, display_chord_short, display_key

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


class ChordText(MusicText):

    def play(
        self,
        music_data: MusicData,
        color: ManimColor = WHITE,  # Leaving as `None` will keep same color as initial
        font_size: int = None,  # Leaving as `None` will keep same font_size as initial
    ) -> Animation:
        return PlayMusicText(
            [
                MusicTextState(
                    chord_info.time,
                    display_chord_short(chord_info.elem),
                    color,
                    font_size,
                )
                for chord_info in music_data.chords
            ],
            music_text=self,
        )


class KeyText(VGroup):

    group: VGroup
    label: Text
    display: MusicText

    def __init__(
        self,
        label_color: ManimColor = WHITE,
        label_text: str = "Key: ",
        display_color: ManimColor = WHITE,
        display_text: str = "dummy",
        *args,
        font_size: float = DEFAULT_FONT_SIZE,
        **kwargs,
    ):
        super().__init__()
        self.label = Text(
            label_text, font_size=font_size, color=label_color, *args, **kwargs
        )
        self.add(self.label)
        self.display = MusicText(
            display_text, font_size=font_size, color=display_color, *args, **kwargs
        ).next_to(self.label, RIGHT, aligned_edge=DOWN)
        self.add(self.display)

    def play(
        self,
        music_data: MusicData,
        color: ManimColor = WHITE,  # Leaving as `None` will keep same color as initial
    ) -> Animation:
        return PlayMusicText(
            [
                MusicTextState(
                    key_info.time,
                    display_key(key_info.elem),
                    color,
                )
                for key_info in music_data.keys
            ],
            music_text=self.display,
        )


class LyricText(MusicText):

    highlight_syllables: bool
    syllable_join_str: str
    syllable_active_color: str
    syllable_inactive_color: str

    DEFAULT_SYLLABLE_JOIN_STR = "-"
    DEFAULT_SYLLABLE_JOIN_COLOR = "gray"
    DEFAULT_SYLLABLE_INACTIVE_COLOR = "gray"
    DEFAULT_SYLLABLE_ACTIVE_COLOR = "white"

    def __init__(
        self,
        *args,
        highlight_syllables: bool = False,
        syllable_join_str: str = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.highlight_syllables = highlight_syllables
        self.syllable_join_str = (
            r"{\color{"
            + self.DEFAULT_SYLLABLE_JOIN_COLOR
            + r"}"
            + (
                syllable_join_str
                if syllable_join_str is not None
                else self.DEFAULT_SYLLABLE_JOIN_STR
            )
            + r"}"
        )
        # TODO: allow customizing color
        self.syllable_active_color = self.DEFAULT_SYLLABLE_ACTIVE_COLOR
        self.syllable_inactive_color = self.DEFAULT_SYLLABLE_INACTIVE_COLOR

    def play(
        self,
        music_data: MusicData,
        color: ManimColor = WHITE,  # Leaving as `None` will keep same color as initial
        font_size: int = None,  # Leaving as `None` will keep same font_size
    ) -> Animation:
        # TODO: might be cool if new lyrics swept in from the right side while bumping out old lyrics to the left, instead

        # Helper functions
        def get_syllable_texstr(syl_text: str, emph: bool) -> str:
            if emph:
                return r"{\color{" + self.syllable_active_color + r"}" + syl_text + r"}"
            else:
                return (
                    r"{\color{" + self.syllable_inactive_color + r"}" + syl_text + r"}"
                )

        def get_lyric_syllabized_texstr(
            lyric_syllables: list[MusicDataTiming[str]],
            cur_syl_text: str,
        ) -> str:
            texstr = self.syllable_join_str.join(
                (get_syllable_texstr(syl_info.elem, emph=syl_info.elem is cur_syl_text))
                for syl_info in lyric_syllables
            )
            return texstr

        # Compile a list of intermediate MusicText states
        text_steps: list[MusicTextState] = []

        # simpler case: just each unique word, no syllable stresses
        if not self.highlight_syllables:
            for lyric_info in music_data.lyrics:
                text_steps.append(
                    MusicTextState(
                        time=lyric_info.time,
                        text=self.syllable_join_str.join(
                            syllable_info.elem for syllable_info in lyric_info.elem
                        ),
                        color=color,
                        font_size=font_size,
                    )
                )
        # complex case: should highlight each syllable as it is spoken
        else:
            # loop through all lyrics in the song
            for lyric_info in music_data.lyrics:
                # if there's only one syllable, do an easy step
                if len(lyric_info.elem) == 1:
                    text_steps.append(
                        MusicTextState(
                            time=lyric_info.time,
                            text=lyric_info.elem[0].elem,
                            color=color,
                            font_size=font_size,
                        )
                    )
                    continue
                # make a unique animation step for each syllable in each lyric
                for cur_syl_info in lyric_info.elem:
                    # make a LaTeX text with the current syllable emphasized, and save it
                    text_steps.append(
                        MusicTextState(
                            time=cur_syl_info.time,
                            text=get_lyric_syllabized_texstr(
                                lyric_info.elem, cur_syl_info.elem
                            ),
                            color=color,
                            font_size=font_size,
                        )
                    )
        return PlayMusicText(
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
    time: float
    text: str
    color: ManimColor | None = None  # None means "keep previous"
    font_size: float | None = None  # None means "keep previous"


class PlayMusicText(TimestampedAnimationSuccession):

    def __init__(
        self,
        text: list[MusicTextState],
        music_text: MusicText,  # NOTE: must be a dummy object with the desired position and SOME POINTS, even if they're transparent
        transition_time: float = 0.1,  # in seconds
        **kwargs,
    ):
        if len(text) == 0:
            return None
        # TODO: figure out how to set frame-0 text if in offset 0 from `text` param
        # TODO: figure out how to specify position / color / etc if not passing a template object in
        # TODO: left alignment?

        anims: list[tuple[float, Animation]] = []
        previous_color = music_text.color
        previous_font_size = music_text._original_font_size

        for text_state in text:
            # create animation for this latest text value
            color = previous_color = text_state.color or previous_color
            font_size = previous_font_size = text_state.font_size or previous_font_size
            new_music_text = MusicText(
                text_state.text,
                color=color,
                font_size=font_size,
            ).move_to(music_text)
            anim = Transform(music_text, new_music_text)
            anims.append((text_state.time, anim))

        super().__init__(anims, transition_time, **kwargs)


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
        # print(music_text.get_center())
        # music_text2 = MusicalText("").move_to(UP * -1 + RIGHT * -1)
        # print(music_text2.get_center())
        # print(music_text2.points)
        # self.play(Create(music_text))
        self.add(music_text)
        self.wait(1)

        updates = [MusicTextState(i / 3, f"Second {i:.2}") for i in range(50)]
        self.play(PlayMusicText(updates, music_text, transition_time=5))
        self.wait(1)
