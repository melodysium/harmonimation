from music21.common.types import OffsetQL

from musicxml import MusicData, MusicDataTiming

# TODO: make configurable
DEFAULT_EXTRA_START_TIME_SEC = 2  # seconds


def resolve_timing(music_data: MusicData) -> None:  # modify in place
    # TODO: maybe some smart way of finding all MusicDataTiming objects in MusicData?
    for timing in music_data.all_notes:
        _set_timing_sec(timing)
    for part_timings in music_data.all_notes_by_part.values():
        for timing in part_timings:
            _set_timing_sec(timing)
    # TODO: set timing on bpm
    for timing in music_data.chords:
        _set_timing_sec(timing)
    # TODO: set timing on comments
    for timing in music_data.lyrics:
        _set_timing_sec(timing)
        for lyric_syllable in timing.elem:
            _set_timing_sec(lyric_syllable)
    for timing in music_data.keys:
        _set_timing_sec(timing)
    for timing in music_data.chord_roots:
        _set_timing_sec(timing)


def _beat_to_sec(beat: OffsetQL) -> float:
    # TODO: handle changing BPM
    bpm = 180  # TODO: actually parse from music_data!
    bps = bpm / 60
    second = beat / bps
    return second + DEFAULT_EXTRA_START_TIME_SEC


def _set_timing_sec(timing: MusicDataTiming) -> None:  # modify in place
    timing.time = _beat_to_sec(timing.offset)
