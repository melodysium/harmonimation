@tool

extends Node


var DEFAULT_FONT := preload("res://assets/Hack-Regular.ttf")

var MUSIC_DATA: Dictionary[String, Array] = json_to_dict("res://assets/my_time_data.json") # TODO: fix typing


func print_err(...args: Array) -> void:
	print_rich("[color=red]", "".join(args), "[/color]")


func json_to_dict(json_file: String) -> Variant: # Optional[Dictionary]
	var json_string := FileAccess.get_file_as_string(json_file)
	var json := JSON.new()
	var error := json.parse(json_string)
	if error != OK:
		print_err("ERROR(json_to_dict): JSON Parse Error: ", json.get_error_message(), " in ", json_string, " at line ", json.get_error_line())
		return null;
	if typeof(json.data) == TYPE_DICTIONARY:
		return json.data
	else:
		print_err("ERROR(json_to_dict): Unexpected json data type: " + type_string(typeof(json.data)))
		return null


## Fill an array with the same element n times.
## WARNING: `elem` is not copied when adding. Modifying the element will modify all elements of the array.
func fill_array(size: int, elem: Variant) -> Array:
	print_verbose("start Utils.fill_array(size=%s, elem=%s)" % [size, elem])
	var arr := []
	for i in range(size):
		arr.append(elem)
	print_verbose("end Utils.fill_array(), return=%s" % [arr])
	return arr


## Represents a single Pitch name, with multiple ways of displaying it as a string.
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
