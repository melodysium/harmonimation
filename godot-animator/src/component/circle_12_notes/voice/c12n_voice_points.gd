@tool

# TODO: fancy animations like: fade in, sweep when hit by connector, etc

class_name C12NVoicePoints
extends HarmonimationWidget


#region types and consts

## Circle radius for pitch circles
const BASE_PITCH_CIRCLE_RADIUS := 0.2

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

#@export
## Colors used for pitch highlight circles. Start transparent. Indexed by pitch_class.
var pitch_circle_colors: Array[Color] = Array(Utils.fill_array(12, Color.TRANSPARENT), TYPE_COLOR, "", null):
	set(val):
		# TODO: This property seems unable to be reset at all in the editor. Maybe add a manual "reset" button? Maybe investigate resetting arrays in properties?
		print_verbose("pitch_circle_colors.set(val=%s), oldval=%s" % [val, pitch_circle_colors])
		if val == null:
			Utils.print_err("[color=red]WARNING: pitch_circle_colors requires a non-null array, but null provided. Ignoring.[/color]" % val.size())
			return
		if val.size() != 12:
			Utils.print_err("[color=red]WARNING: pitch_circle_colors requires an array of 12 elements, but provided one has size()=%s. Ignoring.[/color]" % val.size())
			return
		if val.any(func(elem: Variant) -> bool: return elem is not Color):
			Utils.print_err("[color=red]WARNING: pitch_circle_colors requires an array of Color elements, but provided one some non-Color elements. Ignoring.[/color]" % val.size())
			return
		pitch_circle_colors = val
		if self._pitch_circle_nodes != null and self._pitch_circle_nodes.size() == 12:
			_configure_pitch_circle_nodes()

#endregion


#region Internal state

## Parent node expected to be C12nVoice. Will be null otherwise.
var _voice: C12NVoice

var _c12n: Circle12Notes:
	get():
		if _voice == null:
			printerr("C12NVoicePoints._c12n: tried to get, but _c12n is null!")
			return null;
		return _voice._c12n
	set(val):
		printerr("C12NVoicePoints._c12n is a convenience getter, not a variable to set!")

## Mapping of pitch_class to pitch circles
var _pitch_circle_nodes: Dictionary[int, Circle2D] = {}

### Mapping of pitch_class to pitch labels
#var _pitch_text_nodes: Dictionary[int, Text2D] = {}

#endregion


func _enter_tree() -> void:
	var parent := get_parent()
	if parent is not C12NVoice:
		printerr("C12NVoicePoints expects to be a child of a C12NVoice node, but instead this is child of a {} node called {}" % [typeof(parent), parent.name])
		return
	_voice = parent

func _ready() -> void:
	if not _c12n.is_node_ready():
		await _c12n.ready

	# Construct child nodes
	for pitch_info: Circle12Notes.PitchInfo in _c12n._list_positions():

		# Pitch circle
		var circle := Circle2D.new(
			_c12n.radius * BASE_PITCH_CIRCLE_RADIUS,
			Color.WHITE,
			false,
			_c12n.radius * .02 # TODO: make into constant or configurable
		)
		_pitch_circle_nodes[pitch_info.pitch_class] = circle
		_c12n.add_child(circle, true)
		#circle.visible = false # start off by default
		#circle.position = pitch_info.pos
	
	self._move_pitch_nodes()
	self._configure_pitch_circle_nodes()
	
	# re-compute layout whenever necessary
	_c12n.connect("layout_changed", _move_pitch_nodes)
	
	# connect animation signals
	super._connect_signals()


#region Private helpers

func _move_pitch_nodes() -> void:
	if not is_node_ready():
		return
	for pitch_info: Circle12Notes.PitchInfo in _c12n._list_positions():
		_pitch_circle_nodes[pitch_info.pitch_class].position = pitch_info.pos

func _configure_pitch_circle_nodes() -> void:
	print_verbose("start _configire_pitch_circle_nodes(). _pitch_circle_nodes=%s, pitch_circle_colors=%s" % [_pitch_circle_nodes, pitch_circle_colors])
	for i in range(12):
		_pitch_circle_nodes[i].color = pitch_circle_colors[i]

#endregion


#region animations

## Given structured information about the song, create a list of animations to play at set times.
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep]:
	print_verbose("C12NVoice.hrmn_animate(): start")
	var animations: Array[Utils.AnimationStep] = []

	## animate chord roots
	print_verbose("hrmn_animate(): animating chord roots")
	var chord_roots: Array[Dictionary] = Array(Utils.as_array(music_data["chord_roots"]), TYPE_DICTIONARY, "", null)
	animations.append_array(animate_chord_roots(chord_roots))

	# TODO: animate notes played
	
	print_verbose("C12NVoice.hrmn_animate(): end")
	return animations


func animate_chord_roots(chord_roots: Array[Dictionary]) -> Array[Utils.AnimationStep]:
	print_verbose("animate_chord_roots(): start")
	var anims: Array[Utils.AnimationStep] = []


	var selected_pitches: Array[int] = []
	var previous_pitch_circle_colors := pitch_circle_colors
	var previous_selected_pitch_class := -1 # -1 = none, 0-11 = selected

	for chord_root: Dictionary in chord_roots:
		var time: float = chord_root["time"]
		var new_pitch_class: int = chord_root["elem"]["pitchClass"]

		if new_pitch_class == previous_selected_pitch_class:
			# same pitch, no need to animate
			continue
		
		# record this pitch in the selected_pitches array
		selected_pitches.insert(0, new_pitch_class)
		if _voice.max_active != null and selected_pitches.size() > _voice.max_active.v:
			selected_pitches.pop_back()
		# create a new pitch_circle_colors for this new selection
		var new_pitch_circle_colors: Array[Color] = Array(Utils.fill_array(12, Color.TRANSPARENT), TYPE_COLOR, "", null)
		var selected_indexes_to_set := range(selected_pitches.size())
		selected_indexes_to_set.reverse()
		for i: int in selected_indexes_to_set:
			var pitch_class := selected_pitches[i]
			#var color := Color(1.0, 1.0, 1.0, 0.6) ** i
			var color := Color.WHITE
			color.a =  pitch_circle_history_alpha_decay_factor ** i
			new_pitch_circle_colors[pitch_class] = color
		anims.append(Utils.AnimationStep.new(self, time - .05, time + .05, [Utils.PropertyChange.new("pitch_circle_colors", previous_pitch_circle_colors, new_pitch_circle_colors)]))

		# update tracking vars for next iteration
		previous_selected_pitch_class = new_pitch_class
		previous_pitch_circle_colors = new_pitch_circle_colors

	print_verbose("animate_chord_roots(): end")
	return anims


#endregion
