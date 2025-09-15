@tool

extends Node


var DEFAULT_FONT := preload("res://assets/Hack-Regular.ttf")

class Pitch:

	# TODO: make into Dictionary[Dictionary[String, Variant]] for more info
	const _PITCH_CLASS_NAME_MAPPING := {
		0: "C",
		1: "D♭",
		2: "D",
		3: "E♭",
		4: "E",
		5: "F",
		6: "G♭",
		7: "G",
		8: "A♭",
		9: "A",
		10: "B♭",
		11: "B",
	}

	# TODO: support customization on sharp/flat, natural, etc
	static func pitchclass_to_pitchname(pitch_class: int) -> String:
		return _PITCH_CLASS_NAME_MAPPING[pitch_class % 12]
