@tool
class_name MusicScoreData
extends Resource

# TODO: get the caching actually working. maybe I need to delay checking until later? why is the export data all null during _init()?
# TODO: if the user selects a different musicxml file during a session, it should trigger a re-load
# TODO: find better more encapsulated way for MusicScoreData to own and update re-processing input file without getting brainrot from checksum being not yet loaded from export when filepath export gets loaded first

## number of bytes for each hash iteration when computing checksum
const HASH_CHUNK_SIZE = 1024

## set to true to always re-compute music_data upon load
const DISABLE_CACHING := false

## filepath to use for sending data from python parser back to godot
const TMP_MUSIC_DATA_JSON_FILEPATH := "tmp_music_data.json"


# TODO: inner classes cannot be exported. need to rip these out. :(


## parsed music data in JSON format, for consumption by animation widgets
@export_storage var _music_data: JSON = null:
	set(val):
		print_verbose("setting _music_data JSON value")
		_music_data = val
		_script_vars_ready["_music_data"] = true
		if val != null:
			_music_data_dict = Utils.json_to_dict(_music_data).v

## checksum of musicxml data that was used to compute the current music_data. if checksum of input_music_data_filepath matches, no need to re-compute.
@export_storage var _input_music_data_checksum: PackedByteArray = []:
	set(val):
		print_verbose("setting _input_music_data_checksum = %s" % val.hex_encode())
		_input_music_data_checksum = val
		_script_vars_ready["_input_music_data_checksum"] = true


# TODO: file watch on this, re-run harmonimation parse on changes
## input score file holding music data
@export_global_file("*.musicxml") var input_music_data_filepath: String = "":
	set(val):
		print_verbose("setting input_music_data_filepath = %s" % val)
		input_music_data_filepath = val
		_script_vars_ready["input_music_data_filepath"] = true
		call_deferred("_manual_ready")


# TODO: make this use setget?
## JSON data available in Dictionary form
var _music_data_dict : Dictionary


func place_in_dict(dict: Dictionary, val: Variant) -> Dictionary: #[String, bool]
	dict[val] = false
	return dict
var _script_vars_ready: Dictionary = (get_script().get_script_property_list()
		.filter(func(prop_dict: Dictionary): return prop_dict.has("usage") and prop_dict["usage"] & PROPERTY_USAGE_STORAGE)
		.map(func(prop_dict: Dictionary): return prop_dict.name)
		.reduce(place_in_dict, {}))


func _init() -> void:
	print_verbose("initializing MusicScoreData. initial state: input_music_data_filepath=%s, _input_music_data_checksum=%s, _music_data=%s" % [input_music_data_filepath, _input_music_data_checksum.hex_encode(), _music_data])
	print_verbose(_script_vars_ready)
	#print_verbose(get_script().get_script_property_list())
	#var thisScript: GDScript = get_script()
	#print_verbose('Exported Properties of "%s":' % [ thisScript.resource_path ])
	#for propertyInfo: Dictionary in thisScript.get_script_property_list():
		#if propertyInfo.has("usage") and propertyInfo["usage"] & PROPERTY_USAGE_STORAGE:
			#var propertyName: String = propertyInfo.name
			#var propertyValue = get(propertyName)
			#print_verbose(' %s = %s' % [ propertyName, propertyValue ])

	# set up fallback load timer to just go ahead, even if export vars seem incomplete
	var _fallback_load: SceneTreeTimer = Engine.get_main_loop().create_timer(1.0)
	_fallback_load.connect("timeout", _handle_fallback_load_timer)


func _handle_fallback_load_timer() -> void:
	print_verbose("_fallback_load timer triggered")
	_force_recalculate()


## externally controlled trigger to "wake up" and detect whether input file should be parsed
func _manual_ready() -> void:
	# check for data not yet loaded
	if _script_vars_ready.values().any(func(b: bool): return b != true):
		print_verbose("detected incomplete export var loading. skipping _manual_ready().")
		return
	_force_recalculate()

## assume all exports are loaded, go ahead with calculation
func _force_recalculate() -> void:
	print_verbose("_force_recalculate: input_music_data_filepath=%s, _input_music_data_checksum=%s, _music_data=%s" % [input_music_data_filepath, _input_music_data_checksum.hex_encode(), _music_data])
	# if input filename is empty, clear data and exit
	if input_music_data_filepath == null or input_music_data_filepath == "":
		_input_music_data_checksum = []
		_music_data = null
		emit_changed()
		return

	# early indicators that we need to re-compute
	if _music_data == null:
		print_verbose("missing _music_data for input file %s; re-parsing music score data" % input_music_data_filepath)
		_proprocess_and_save_music_data(_compute_checksum(input_music_data_filepath))
	if DISABLE_CACHING:
		print_verbose("checksum-based caching of music_data disabled; re-parsing music score data")
		_proprocess_and_save_music_data(_compute_checksum(input_music_data_filepath))

	# check if we need to re-compute music_data
	print_verbose("computing checksum of previous music score data. previous: %s" % _input_music_data_checksum.hex_encode())
	var new_checksum = _check_input_changed(input_music_data_filepath, _input_music_data_checksum)
	if new_checksum.size() == 0:
		print_verbose("checksum identical; skipping re-parse")
		return
	else:
		print_verbose("checksum of file %s (%s) differs from previously saved checksum (%s); re-parsing music score data" % [input_music_data_filepath, new_checksum, _input_music_data_checksum])

	# file has changed from last compute, need to re-compute
	_proprocess_and_save_music_data(new_checksum)


## parse input music data, save results and checksum
func _proprocess_and_save_music_data(new_checksum: PackedByteArray) -> void:
	_music_data = _parse_input_music_data(input_music_data_filepath)
	_input_music_data_checksum = new_checksum
	emit_changed()


## invoke shell commands to parse input_music_data_filepath via python script into music_data
func _parse_input_music_data(input_path: String) -> JSON:
	# Validate input file
	if not FileAccess.file_exists(input_path):
		printerr("_parse_input_music_data: file %s is invalid" % input_path)
		return null

	# Invoke python script for processing musicxml into music_data JSON
	var output: Array[String]
	if OS.has_feature("windows"):
		print_verbose("detected win environment, invoking python via CMD.exe")
		output = _invoke_python_win(input_path)
	elif OS.has_feature("macos"):
		print_verbose("detected macos environment, invoking python via /bin/sh")
		output = _invoke_python_mac(input_path)
	else:
		printerr("Unknown platform. Skipping python musicxml parse. Harmonimation will not work yet!") # TODO: print platform tags
		return null
	for line in output:
		print_verbose(line)
#
	# Load created JSON file into this resource
	var json_string := FileAccess.get_file_as_string(TMP_MUSIC_DATA_JSON_FILEPATH)
	var music_data = JSON.new()
	var error := music_data.parse(json_string)
	if error != OK:
		printerr("_parse_input_music_data: JSON Parse Error: ", music_data.get_error_message(), " in ", json_string, " at line ", music_data.get_error_line())
		return null;
#
	# JSON loaded; delete the file
	DirAccess.remove_absolute(TMP_MUSIC_DATA_JSON_FILEPATH)
#
	return music_data


func _invoke_python_win(input_path: String) -> Array[String]:
	# Invoke Command Prompt to:
	# 1) load python virtual environment, then
	# 2) invoke harmonimation python script to parse input musicxmlf ile
	var output: Array[String] = []
	var cmd_to_execute = """\
		..\\.venv-win\\Scripts\\activate.bat \
		&& python3 ..\\renderer\\main.py --music-data-file \"%s\" \"%s\"""" % [TMP_MUSIC_DATA_JSON_FILEPATH, input_path]
	print_verbose("Invoking external python script on Windows via `CMD.exe`, please wait...")
	print_verbose("command: %s" % cmd_to_execute)
	OS.execute("CMD.exe", ["/C", cmd_to_execute], output, true)
	return output


func _invoke_python_mac(input_path: String) -> Array[String]:
	var output: Array[String] = []
	var cmd_to_execute = """\
		source ../.venv/bin/activate \
		&& python3 ../renderer/main.py --music-data-file \'%s\' \'%s\'""" % [TMP_MUSIC_DATA_JSON_FILEPATH, input_path]
	print_verbose("Invoking external python script on Mac via `/bin/sh`, please wait...")
	print_verbose("command: %s" % cmd_to_execute)
	OS.execute("/bin/sh", ["-c", cmd_to_execute], output, true)
	return output


## Compute a checksum of provided data
func _compute_checksum(filepath: String) -> PackedByteArray:
	print_verbose("_compute_checksum(%s)" % filepath)
	# Check that file exists.
	if not FileAccess.file_exists(filepath):
		printerr("cannot compute checksum: file %s is invalid" % filepath)
		return []
	# Start an SHA-256 context.
	var ctx = HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	# Open the file to hash.
	var file = FileAccess.open(filepath, FileAccess.READ)
	# Update the context after reading each chunk.
	while file.get_position() < file.get_length():
		var remaining = file.get_length() - file.get_position()
		ctx.update(file.get_buffer(min(remaining, HASH_CHUNK_SIZE)))
	# Get the computed hash.
	var res := ctx.finish()
	# Print the result as hex string and array.
	print_verbose("_compute_checksum: hash result, hex: ", res.hex_encode()) # , "int: ", Array(res)
	return res


## Determine if we need to re-compute music data based on file change. null = no change,
func _check_input_changed(input_filepath: String, checksum: PackedByteArray) -> PackedByteArray:
	# if no previous checksum, yes we need to re-compute
	if checksum.size() == 0:
		return _compute_checksum(input_filepath)
	# compute new checksum
	var file_checksum = _compute_checksum(input_filepath)
	if file_checksum.size() == 0:
		# file is invalid. panic?
		return [] # can't recompute if file is invalid
	if file_checksum == checksum:
		return [] # no change, no re-compute necessary
	else:
		return file_checksum
