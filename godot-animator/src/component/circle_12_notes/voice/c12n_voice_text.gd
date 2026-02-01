@tool

# TODO: fancy animations like: fade in, sweep when hit by connector, etc

class_name C12NVoiceText
extends HarmonimationWidget


#region types and consts

# TODO: make these user customizable
# TODO: make it possible to customize pitch colors based on other things: instruments playing that note, etc
var DEFAULT_NOTE_IN_KEY_COLOR := Color.WHITE
var DEFAULT_NOTE_NOT_IN_KEY_COLOR := Color.DARK_GRAY

## Font size for pitch names
const BASE_PITCH_NAME_FONT_SIZE := 12

#endregion


#region User Config

## Node to duplciate and create at each endpoint
@export
var template: NodePath

## Multiplicative alpha decay for previously selected pitch circles. Lower number = fade faster.
@export_range(0.0, 1.0, 0.01)
var pitch_circle_history_alpha_decay_factor := 0.6

#endregion


#region Animation Primitives

##@export
### Colors used for pitch label text. Start solid white. Indexed by pitch_class.
#var pitch_text_colors: Array[Color] = Array(Utils.fill_array(12, DEFAULT_NOTE_IN_KEY_COLOR), TYPE_COLOR, "", null):
	#set(val):
		## TODO: This property seems unable to be reset at all in the editor. Maybe add a manual "reset" button? Maybe investigate resetting arrays in properties?
		#print_verbose("pitch_text_colors.set(val=%s), oldval=%s" % [val, pitch_text_colors])
		#if val == null:
			#Utils.print_err("[color=red]WARNING: pitch_text_colors requires a non-null array, but null provided. Ignoring.[/color]" % val.size())
			#return
		#if val.size() != 12:
			#Utils.print_err("[color=red]WARNING: pitch_text_colors requires an array of 12 elements, but provided one has size()=%s. Ignoring.[/color]" % val.size())
			#return
		#if val.any(func(elem: Variant) -> bool: return elem is not Color):
			#Utils.print_err("[color=red]WARNING: pitch_text_colors requires an array of Color elements, but provided one some non-Color elements. Ignoring.[/color]" % val.size())
			#return
		#pitch_text_colors = val
		#if self._pitch_text_nodes != null and self._pitch_text_nodes.size() == 12:
			#_configure_pitch_text_nodes()

#endregion


#region Internal state

## Parent node expected to be C12nVoice. Will be null otherwise.
@onready
var _voice: C12NVoice

var _c12n: Circle12Notes:
	get():
		if _voice == null:
			printerr("C12NVoiceText._c12n: tried to get, but _c12n is null!")
			return null;
		return _voice._c12n
	set(val):
		printerr("C12NVoiceText._c12n is a convenience getter, not a variable to set!")

## Mapping of pitch_class to pitch labels
var _pitch_text_nodes: Dictionary[int, Text2D] = {}

#endregion

func _enter_tree() -> void:
	var parent := get_parent()
	if parent is not C12NVoice:
		printerr("C12NVoiceText expects to be a child of a C12NVoice node, but instead this is child of a {} node called {}" % [typeof(parent), parent.name])
		return
	_voice = parent


func _ready() -> void:
	if not _c12n.is_node_ready():
		await _c12n.ready

	# Construct child nodes
	for pitch_info: Circle12Notes.PitchInfo in _c12n._list_positions():
		# Pitch text
		var pitch_name := Utils.Pitch.pitchclass_to_pitchname(pitch_info.pitch_class)
		var text := Text2D.new(
			Utils.DEFAULT_FONT,
			pitch_name,
			HORIZONTAL_ALIGNMENT_CENTER,
			VERTICAL_ALIGNMENT_CENTER,
			5000,
			BASE_PITCH_NAME_FONT_SIZE,
			Color.WHITE
		)
		text.name = "C12NText_%s" % [pitch_name]
		_pitch_text_nodes[pitch_info.pitch_class] = text
		_c12n.add_child(text, true)
		text.position = pitch_info.pos
		#print("PitchInfo(pitch_class=%s, pos=%s)" % [pitch_info.pitch_class, pitch_info.pos])
		#print("text.global_position=%s" % text.global_position)

	self._move_pitch_nodes()
	self._configure_pitch_text_nodes()
	
	# re-compute layout whenever necessary
	_c12n.connect("layout_changed", _move_pitch_nodes)
	
	## connect animation signals
	#super._connect_signals()

#region Private helpers

func _move_pitch_nodes() -> void:
	if not is_node_ready():
		return
	for pitch_info: Circle12Notes.PitchInfo in _c12n._list_positions():
		_pitch_text_nodes[pitch_info.pitch_class].position = pitch_info.pos

func _configure_pitch_text_nodes() -> void:
	print_verbose("start _configure_pitch_text_nodes(). _pitch_text_nodes=%s" % [_pitch_text_nodes])
	for i in range(12):
		_pitch_text_nodes[i].text = Utils.Pitch.pitchclass_to_pitchname(i)
		#_pitch_text_nodes[i].modulate_color = pitch_text_colors[i]


## Given an array of pitch classes which are in a key, compute the colors that should be used when displaying those pitches
func _compute_pitch_text_colors(pitches: Array[int]) -> Array[Color]:
	var pitch_text_colors_val: Array[Color] = []
	for i in range(12):
		var pitch_in_key := pitches.has(i)
		if pitch_in_key:
			pitch_text_colors_val.append(DEFAULT_NOTE_IN_KEY_COLOR)
		else:
			pitch_text_colors_val.append(DEFAULT_NOTE_NOT_IN_KEY_COLOR)
	return pitch_text_colors_val

#endregion


#region animations

## Given structured information about the song, create a list of animations to play at set times.
## Full return type: Dictionary[Node, Dictionary[String(property), Array[Keyframe]]
func hrmn_animate(music_data: Dictionary) -> Dictionary[Node, Dictionary]:
	print_verbose("C12NVoice.hrmn_animate(): start")
	var animations: Dictionary[Node, Dictionary] = {}

	# animate key changes
	print_verbose("hrmn_animate(): animating key changes")
	var keys: Array[Dictionary] = Array(Utils.as_array(music_data["keys"]), TYPE_DICTIONARY, "", null)
	animations = Utils.merge_animations(animations, animate_key_changes(keys))
	
	print_verbose("C12NVoice.hrmn_animate(): end")
	return animations


func animate_key_changes(keys: Array[Dictionary]) -> Dictionary[Node, Dictionary]:
	print_verbose("animate_key_changes(): start")

	# build a sequence of rotation animations to play
	var anims: Dictionary[Node, Dictionary] = {}
	# track previous key to skip duplicates
	var previous_key: Array[int] = Array(Utils.as_array(keys[0]["elem"]["pitches"]), TYPE_INT, "", null)
	# track colors from previous chord to skip any 
	var previous_pitch_text_colors: Array[Color] = _compute_pitch_text_colors(previous_key)
	# add keyfames at time 0
	for i in range(12):
		anims[_pitch_text_nodes[i]] = {"modulate_color": [Utils.PropertyKeyframePoint.new(previous_pitch_text_colors[i], 0)]}

	for key: Dictionary in keys.slice(1):

		# figure out start and end time for the main key change animation
		var target_end_time: float = key["time"]

		# detect if root changed
		var root_pitch_class: int = key["elem"]["pitch"]["pitchClass"]
		if key["elem"]["quality"] == "minor":
			root_pitch_class = (root_pitch_class + 3) % 12

		# color individual pitches based on key
		var new_pitch_text_colors: Array[Color] = _compute_pitch_text_colors(
			Array(Utils.as_array(key["elem"]["pitches"]), TYPE_INT, "", null))
		# only do anything if the colors changed
		if new_pitch_text_colors != previous_pitch_text_colors:
			for i in range(12):
				anims[_pitch_text_nodes[i]]["modulate_color"].append(
					Utils.PropertyKeyframePoint.new(new_pitch_text_colors[i], target_end_time, 0.0, _c12n.transition_time, -4.0))
			# set animations for each pitch
			previous_pitch_text_colors = new_pitch_text_colors

	print_verbose("animate_key_changes(): end")
	return anims


#endregion
