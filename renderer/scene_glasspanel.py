# standard libs


# 3rd party libs
from manim import *

# project files
from musicxml import MusicData, MusicDataTiming
from obj_music_circles import Circle12NotesSequenceConnectors, PlayCircle12Notes
from obj_rhythm_circle import CircleRhythm
from obj_music_text import ChordText, LyricText, NoteText
from utils import get_root


class GlassPanel(Scene):

    music_data: MusicData
    widgets: list[Mobject]

    def __init__(self, music_data: MusicData, widgets: list[Mobject]):
        super().__init__()
        self.music_data = music_data
        self.widgets = widgets

    def construct(self):

        # load necessary data

        self.wait(0.2)

        # run create animations
        def map_create_animation(widget: Mobject) -> Animation:
            if isinstance(widget, Circle12NotesSequenceConnectors):
                return widget.create()
            else:
                return Create(widget)

        create_animations: list[Animation] = list(
            map(map_create_animation, self.widgets)
        )
        self.play(create_animations, run_time=2)

        self.wait(1)

        # run play animations
        def map_play_animation(widget: Mobject) -> Animation:
            if (
                # TODO: make into single "interface"
                isinstance(widget, Circle12NotesSequenceConnectors)
                or isinstance(widget, ChordText)
                or isinstance(widget, LyricText)
            ):
                return widget.play(self.music_data)
            else:
                return None

        play_animations = list(
            filter(lambda x: x is not None, map(map_play_animation, self.widgets))
        )
        self.play(AnimationGroup(play_animations))
