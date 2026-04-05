@tool

class_name LineState
extends Object

var start_pitch: int
var end_pitch: int
var line_promise: NodeProvider.NodePromise # NodeProvider<Line2D>
# TODO: length: float(0.0 - 1.0), from start to end

static func create(
    _start_pitch: int,
    _end_pitch: int,
    _line_promise: NodeProvider.NodePromise
) -> LineState:
    var state := LineState.new()
    state.start_pitch = _start_pitch
    state.end_pitch = _end_pitch
    state.line_promise = _line_promise
    return state

func peek_line() -> Line2D:
    return self.line_promise.peek()

func _to_string() -> String:
    return "LineState(start_pitch=%d, end_pitch=%d, line_promise=%s)" % [start_pitch, end_pitch, line_promise]
