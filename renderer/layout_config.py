# 3rd party
from manim import *
from manim.typing import Vector3D

# project files
from musicxml import MusicData
from obj_music_circles import Circle12NotesSequenceConnectors
from obj_music_text import ChordText, LyricText, KeyText
from utils import get_ionian_root


def _compute_shift(widget_def: dict) -> Vector3D:
    shift_x = float(widget_def.get("shift_x", 0)) * RIGHT
    shift_y = float(widget_def.get("shift_y", 0)) * UP
    return shift_x + shift_y


def _build_text(widget_def: dict) -> Text:
    assert "text" in widget_def
    return Text(
        text=widget_def["text"],
        font_size=widget_def.get("font_size", DEFAULT_FONT_SIZE),
    ).shift(_compute_shift(widget_def))


def _build_chordtext(widget_def: dict) -> ChordText:
    return ChordText(
        "dummy",
        color=ManimColor(None, alpha=0),
        font_size=widget_def.get("font_size", DEFAULT_FONT_SIZE),
    ).shift(_compute_shift(widget_def))


def _build_lyrictext(widget_def: dict) -> LyricText:
    return LyricText(
        "dummy",
        color=ManimColor(None, alpha=0),
        font_size=widget_def.get("font_size", DEFAULT_FONT_SIZE),
        highlight_syllables=widget_def.get("highlight_syllables", False),
        syllable_join_str=widget_def.get("syllable_join_str", None),
    ).shift(_compute_shift(widget_def))


def _build_keytext(widget_def: dict) -> KeyText:
    return KeyText(
        display_text="dummy",
        display_color=ManimColor(None, alpha=0),
        font_size=widget_def.get("font_size", DEFAULT_FONT_SIZE),
    ).shift(_compute_shift(widget_def))


def _build_circle12notes(widget_def: dict, music_data: MusicData) -> list[Mobject]:
    c12n_widgets: list[Mobject] = []  # this method can return 1 or 2 widgets
    radius = widget_def.get("radius", 1.0)
    max_selected_steps = widget_def.get("max_selected_steps", 3)

    # make main circle12notes
    def map_note_intervals(widget_type: str) -> str:
        if widget_type == "circle_chromatic":
            return 1
        elif widget_type == "circle_fifths":
            return 7

    starting_pitch = get_ionian_root(music_data.keys[0].elem).pitchClass

    circle_chromatic = Circle12NotesSequenceConnectors(
        radius=radius,
        max_selected_steps=max_selected_steps,
        steps_per_pitch=map_note_intervals(widget_def["type"]),
        rotate_pitch=starting_pitch,
    ).shift(_compute_shift(widget_def))
    c12n_widgets.append(circle_chromatic)

    # make label, unless it's disabled
    def map_label_text(widget_type: str) -> str:
        if widget_type == "circle_chromatic":
            return "Chromatic circle"
        elif widget_type == "circle_fifths":
            return "Circle of Fifths"

    label_def: dict = widget_def.get(
        "label", {"dummy_ignored": "make dict truthy so it's set as below"}
    )
    if label_def:  # is truthy
        assert isinstance(label_def, dict)
        # label.setdefault("shift_x", 0)
        label_def.setdefault("shift_y", -1.3 * radius)
        label_def.setdefault("font_size", 16 * radius)
        label_def.setdefault("text", map_label_text(widget_def["type"]))
        text_chromatic = (
            Text(
                text=label_def["text"],
                font_size=label_def.get("font_size", DEFAULT_FONT_SIZE),
            )
            .move_to(circle_chromatic)
            .shift(_compute_shift(label_def))
        )
        c12n_widgets.append(text_chromatic)

    # return created widgets
    return c12n_widgets


def build_widgets(config: dict, music_data: MusicData) -> list[Mobject]:
    # TODO: figure out the correct way to report errors from this function
    widgets: list[Mobject] = []

    assert isinstance(config, dict)
    assert "widgets" in config.keys()
    assert isinstance(config["widgets"], list)

    for widget_def in config["widgets"]:

        assert isinstance(widget_def, dict)
        assert "type" in widget_def

        match widget_def["type"]:
            case "text":
                widgets.append(_build_text(widget_def))
            case "circle_chromatic" | "circle_fifths":
                widgets.extend(_build_circle12notes(widget_def, music_data))
            case "chord_text":
                widgets.append(_build_chordtext(widget_def))
            case "lyric_text":
                widgets.append(_build_lyrictext(widget_def))
            case "key_text":
                widgets.append(_build_keytext(widget_def))
            case _:
                raise ValueError("unrecognized widget type")
    return widgets
