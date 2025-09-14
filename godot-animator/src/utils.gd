extends Node

func map(_in: Array[Variant], fn: Callable):
	var _out = Array()
	for e in _in:
		_out.append(fn.call(e))
	return _out
