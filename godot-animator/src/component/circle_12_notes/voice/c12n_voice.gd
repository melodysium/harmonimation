@tool

class_name C12NVoice
extends Node


#region User Config

## Source for pitches and timings, i.e. "chord_roots", "part:Part Name"
@export
var pitch_source: String = "chord_roots" # TODO: figure out a nicer way to configure this

# TODO: remove?
## Base color for all elements related to this voice.
@export
var base_color: Color = Color.WHITE

## Max number of endpoints that can be active. Connectors are limited to n - 1 due to being between endpoints.
@export
var max_active: OptionalInt = null

## Distance from center of circle to place endpoints. If null, will be at the main circle's radius.
@export
var radius: OptionalFloat = null

## Behavior to decay pitch elements over time. If null, leave elements until destroyed by max_active
#@export
#var decay_behavior: DecayBehavior = null # TODO: actually implement and respect

## Multiplicative alpha decay for previously selected pitches. Lower number = fade faster.
@export_range(0.0, 1.0, 0.01)
var alpha_decay_factor := 0.6

#endregion


#region Internal State

## Parent node expected to be Circle12Notes. Will be null otherwise.
var _c12n: Circle12Notes

#endregion

func _enter_tree() -> void:
	var parent := get_parent()
	if parent is not Circle12Notes:
		printerr("C12NVoice._enter_tree(): C12NVoice expects to be a child of a Circle12Notes node, but instead it is child of a {} node called {}" % [typeof(parent), parent.name])
		return
	_c12n = parent
