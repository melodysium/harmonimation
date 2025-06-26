# standard lib
import argparse
from dataclasses import dataclass
import logging

# 3rd party
import pyjson5

# project files
from timing import resolve_timing
from scene_glasspanel import GlassPanel
from layout_config import build_widgets
from musicxml import parse_score_data

# log setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import sys

logger.debug(f"Python version: {sys.version}")
logger.debug(f"Version info: {sys.version_info}")


# --------------------MAIN CONRTOL FLOW--------------------

# TODO: separate out different packages?
# - hrmn_parse
# - hrmn_render
# - hrmn_common
# or at least some folders in the main space here


def parse_args():

    def range_str(txt: str) -> tuple[float, float]:
        range_split = txt.split(",")
        if len(range_split) != 2:
            raise argparse.ArgumentTypeError(
                "Expected a value of format float_1,float_2 (example: 1.5,3)"
            )
        try:
            l, r = range_split
            return (float(l), float(r))
        except ValueError as e:
            raise argparse.ArgumentTypeError(
                f'Invalid value "{txt}". Expected a value of format float_1,float_2 (example: 1.5,3)'
            ) from e

    parser = argparse.ArgumentParser(
        prog="harmonimation",
        description="A program for visualizing musical harmonic analysis",
        epilog="Created by melodysium",
    )
    parser.add_argument(
        "musicxml_file",
        type=argparse.FileType(),
        help="musicxml file to render music from",
    )
    parser.add_argument(
        "harmonimation_file",
        type=argparse.FileType(),
        help="harmonimation.json file to configure layout",
    )
    parser.add_argument(
        "-b",
        "--beat-range",
        type=range_str,
        help="A beat range (inclusive) of the form x,y where x and y are floats (0-indexed). Will only render elements between beats [x, y] in the original piece.",
    )
    parser.add_argument(
        "-t",
        "--time-range",
        type=range_str,
        help="A time range (inclusive) of the form x,y where x and y are floats. Will only render elements between time [x, y] in the final animation.",
    )
    args = parser.parse_args()
    if args.beat_range is not None and args.time_range is not None:
        # TODO: figure out how to print this nicer
        raise argparse.ArgumentError(
            argument=None,
            message="Cannot provide both --beat-range and --time-range arguments.",
        )
    return args


def main():
    # parse program arguments
    args = parse_args()

    # parse music data
    music_data = parse_score_data(args.musicxml_file.read())

    # parse into timing data. (data, beat) -> (data, beat, second). filter if needed.
    if args.beat_range:
        music_data = music_data.filter_by_beat_range(*args.beat_range)
    resolve_timing(music_data)
    if args.time_range:
        # TODO: compensate for create time and start buffer time?
        music_data = music_data.filter_by_time_range(*args.time_range)
    # print(music_data)

    # make harmonimation widgets
    widgets = build_widgets(
        config=pyjson5.load(args.harmonimation_file),
        music_data=music_data,
    )

    # make harmonimation scene, and render!
    GlassPanel(music_data, widgets).render()


if __name__ == "__main__":
    main()
