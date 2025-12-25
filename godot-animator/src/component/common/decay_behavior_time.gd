@tool

class_name DecayBehaviorTime
extends DecayBehavior

## Amount of time new elements will be shown on screen
@export
var duration: float

## "Easing" set in the AnimationPlayer keyframe starting this decay
@export
var easing: float
# TODO confirm: (0, 1) is "ease in", (1, +inf) is "ease out", (-1, 0) is "ease out in", (-inf, -1) is "ease in out"
