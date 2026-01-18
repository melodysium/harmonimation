@tool

class_name LineState
extends Object

var start_pitch: int
var end_pitch: int
var line: Line2D
# TODO: length: float(0.0 - 1.0), from start to end

static func create(
	_start_pitch: int,
	_end_pitch: int,
	_line: Line2D
) -> LineState:
	var state := LineState.new()
	state.start_pitch = _start_pitch
	state.end_pitch = _end_pitch
	state.line = _line
	return state

func _to_string() -> String:
	return "LineState(start_pitch=%d, end_pitch=%d, line=%s)" % [start_pitch, end_pitch, line]
