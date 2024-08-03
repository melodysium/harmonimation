from typing import Any
import math
import numpy as np

from manim import Mobject, Group, Scene, VDict, PI


def callback_add_to_group(group: Group, object: Mobject):
    def callback(scene: Scene) -> None:
        group.add(object)
    return callback


def callback_add_to_vdict(vdict: VDict, index: Any, object: Mobject):
    def callback(scene: Scene) -> None:
        vdict[index] = object
    return callback


# TODO: use Circle.point_at_angle?
def vector_on_unit_circle(t: float):
  return np.array([math.cos(2*PI*t), math.sin(2*PI*t), 0])

def vector_on_unit_circle_clockwise_from_top(t: float):
  return vector_on_unit_circle(1/4 - t)