@tool

class_name Circle12Notes

extends HarmonimationWidget

#region constants and types

# TODO: make some of these configurable?

## Font size for pitch names
const BASE_PITCH_NAME_FONT_SIZE := 12

## Circle radius for pitch circles
const BASE_PITCH_CIRCLE_RADIUS := 0.2

## Default time before a new key change when the Circle will start rotating
const DEFAULT_ROTATE_TRANSITION_TIME = 0.3

## Angle (in radians) for one step of twelve around the circle
const ONE_STEP_ANGLE := TAU / 12

## Tuple of (pitch class [0-11], position (Vec2 relative to center))
class PitchInfo:
	var pitch_class: int
	var pos: Vector2

	func _init(_pitch_class: int, _pos: Vector2) -> void:
		self.pitch_class = _pitch_class
		self.pos = _pos

	func _to_string() -> String:
		return "PitchInfo[pcls=%s, pos=%s]" % [self.pitch_class, self.pos]

#endregion


#region user config exports

# TODO: whether to orient tonic or ionian root at top should be a config option

@export_group("User Config")

## Radius for main circle / pitch names
@export_range(0, 100, 1.0, "or_greater")
var radius := 50.0:
	set(val):
		radius = val
		if _background_circle_node != null:
			_background_circle_node.radius = val
		if _rotate_arc != null:
			_rotate_arc.radius = val
		_move_pitch_nodes()


## Number of pitches advanced every step once clockwise.
## Note this is equivalent to number of steps for one half-note increase in pitch, at least for values [1, 5, 7, 11]
# due to n^2 % 12 == 1. advancing n pitches across n steps results in getting to pitch n+1 at the end.
@export_range(1, 11, 1.0)
var pitches_per_step := 1:
	set(val):
		if ![1, 5, 7, 11].has(val):
			Utils.print_err("WARNING: Circle12Notes currently only supports pitches_per_step values of [1, 5, 7, 11], but you picked: %s. Ignoring." % val)
			return
		pitches_per_step = val
		_move_pitch_nodes()

## First pitch class at the "top" of the node. 0 = C, 1 = Db, ... 11 = B
@export_range(0, 11, 1.0)
var first_pitch_class := 0:
	set(val):
		first_pitch_class = val
		_move_pitch_nodes()

## Color of an arc which will expand to indicate an impending rotation
@export
var rotate_arc_color := Color.ROYAL_BLUE:
	set(val):
		rotate_arc_color = val
		if self._rotate_arc != null:
			self._rotate_arc.color = val

## Time before a new key change when the Circle will start rotating
@export_range(0.0, 2.0, 0.01, "or_greater")
var transition_time := DEFAULT_ROTATE_TRANSITION_TIME

## Number of pitch circles to have selected at once
@export_range(1, 12, 1.0)
var num_pitch_circles_selectable := 3

## Multiplicative alpha decay for previously selected pitch circles. Lower number = fade faster.
@export_range(0.0, 1.0, 0.01)
var pitch_circle_history_alpha_decay_factor := 0.6


#endregion


#region animation primitives

# TODO: re-enable these as exports to mess with. but handle the issue where loading initial state would trigger animations weirdly? put them in reset tracks?
#@export_group("Raw Animation Primitives")

#@export_range(-TAU, TAU, 0.01, "or_less", "or_greater")
## Rotate angle (keeps note text oriented upwards)
var rotate_angle := 0.0:
	set(val):
		#print("rotate_angle.set(val=%f), oldval=%f" % [val, rotate_angle])
		## if < 0 or >= TAU (radians), cycle back within that range
		#if val <= -TAU or val >= TAU:
			#print_verbose("trying to wrap, should come out as %f" % fmod(val, TAU))
			#val = fmod(val, TAU)
		rotate_angle = val
		_move_pitch_nodes()

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

# TODO: make these user customizable
# TODO: make it possible to customize pitch colors based on other things: instruments playing that note, etc
var DEFAULT_NOTE_IN_KEY_COLOR := Color.WHITE
var DEFAULT_NOTE_NOT_IN_KEY_COLOR := Color.DARK_GRAY
#@export
## Colors used for pitch label text. Start solid white. Indexed by pitch_class.
var pitch_text_colors: Array[Color] = Array(Utils.fill_array(12, DEFAULT_NOTE_IN_KEY_COLOR), TYPE_COLOR, "", null):
	set(val):
		# TODO: This property seems unable to be reset at all in the editor. Maybe add a manual "reset" button? Maybe investigate resetting arrays in properties?
		print_verbose("pitch_text_colors.set(val=%s), oldval=%s" % [val, pitch_text_colors])
		if val == null:
			Utils.print_err("[color=red]WARNING: pitch_text_colors requires a non-null array, but null provided. Ignoring.[/color]" % val.size())
			return
		if val.size() != 12:
			Utils.print_err("[color=red]WARNING: pitch_text_colors requires an array of 12 elements, but provided one has size()=%s. Ignoring.[/color]" % val.size())
			return
		if val.any(func(elem: Variant) -> bool: return elem is not Color):
			Utils.print_err("[color=red]WARNING: pitch_text_colors requires an array of Color elements, but provided one some non-Color elements. Ignoring.[/color]" % val.size())
			return
		pitch_text_colors = val
		if self._pitch_text_nodes != null and self._pitch_text_nodes.size() == 12:
			_configure_pitch_text_nodes()

## Origin angle for arc that expands from current top-pitch to new top-pitch before rotating
var rotate_arc_start_angle := 0.0:
	set(val):
		#print("rotate_arc_start_angle.set(val=%f), oldval=%f" % [val, rotate_arc_start_angle])
		rotate_arc_start_angle = val
		if self._rotate_arc != null:
			self._rotate_arc.start_angle = val

## Destination angle for arc that expands from current top-pitch to new top-pitch before rotating
var rotate_arc_end_angle := 0.0:
	set(val):
		#print("rotate_arc_end_angle.set(val=%f), oldval=%f" % [val, rotate_arc_end_angle])
		rotate_arc_end_angle = val
		if self._rotate_arc != null:
			self._rotate_arc.end_angle = val


#endregion


#region onready vars

## Background ring underneath pitches
@onready
var _background_circle_node : Circle2D = $BackgroundCircle

## Parent node for dynamically-added pitch text
@onready
var _pitch_text_parent_node : Node2D = $PitchText

## Parent node for dynamically-added pitch circles
@onready
var _pitch_circles_parent_node : Node2D = $PitchCircles

## Arc which appears when showing impending rotations
@onready
var _rotate_arc: Arc2D = $RotateArc

#endregion


#region internal state vars

## Mapping of pitch_class to pitch labels
var _pitch_text_nodes: Dictionary[int, Text2D] = {}

## Mapping of pitch_class to pitch labels
var _pitch_circle_nodes: Dictionary[int, Circle2D] = {}

#endregion


#region private helpers

func _angle_for_pitch_at_top(selected_pitch_class: int, previous_angle: float = 0.0) -> float:
	var diff_pitch_classes := first_pitch_class - selected_pitch_class
	var diff_steps := diff_pitch_classes * pitches_per_step
	var new_angle := diff_steps * (ONE_STEP_ANGLE)
	new_angle += roundf((new_angle - previous_angle) / TAU) * -TAU
	return new_angle

func _circle_start() -> Vector2:
	return Vector2.UP * self.radius

func _list_positions() -> Array[PitchInfo]:
	var positions: Array[PitchInfo] = []
	for i: int in range(12):
		var step := (i * self.pitches_per_step + self.first_pitch_class) % 12
		var pos := _circle_start().rotated(ONE_STEP_ANGLE * i + self.rotate_angle)
		positions.append(PitchInfo.new(step, pos))
	print_verbose("_list_positions(). pitches_per_step=%s; first_pitch_class=%s; rotate_angle=%s; positions=%s" % [pitches_per_step, first_pitch_class, rotate_angle, positions])
	return positions


func _move_pitch_nodes() -> void:
	if not is_node_ready():
		return
	for pitch_info: PitchInfo in _list_positions():
		_pitch_text_nodes[pitch_info.pitch_class].position = pitch_info.pos
		_pitch_circle_nodes[pitch_info.pitch_class].position = pitch_info.pos

func _configure_pitch_circle_nodes() -> void:
	print_verbose("start _configire_pitch_circle_nodes(). _pitch_circle_nodes=%s, pitch_circle_colors=%s" % [_pitch_circle_nodes, pitch_circle_colors])
	for i in range(12):
		_pitch_circle_nodes[i].color = pitch_circle_colors[i]

func _configure_pitch_text_nodes() -> void:
	print_verbose("start _configure_pitch_text_nodes(). _pitch_text_nodes=%s, pitch_text_colors=%s" % [_pitch_text_nodes, pitch_text_colors])
	for i in range(12):
		_pitch_text_nodes[i].text = Utils.Pitch.pitchclass_to_pitchname(i)
		_pitch_text_nodes[i].modulate_color = pitch_text_colors[i]

#endregion


func _ready() -> void:

	# Construct child nodes
	for pitch_info: PitchInfo in _list_positions():

		# Pitch text
		var pitch_name := Utils.Pitch.pitchclass_to_pitchname(pitch_info.pitch_class)
		var text := Text2D.new(
			Utils.DEFAULT_FONT,
			pitch_name,
			HORIZONTAL_ALIGNMENT_CENTER,
			VERTICAL_ALIGNMENT_CENTER,
			5000,
			BASE_PITCH_NAME_FONT_SIZE,
			pitch_text_colors[pitch_info.pitch_class]
		)
		_pitch_text_nodes[pitch_info.pitch_class] = text
		_pitch_text_parent_node.add_child(text, true)
		#text.position = pitch_info.pos
		#print("PitchInfo(pitch_class=%s, pos=%s)" % [pitch_info.pitch_class, pitch_info.pos])
		#print("text.global_position=%s" % text.global_position)

		# Pitch circle
		var circle := Circle2D.new(
			self.radius * BASE_PITCH_CIRCLE_RADIUS,
			Color.WHITE,
			false,
			self.radius * .02
		)
		_pitch_circle_nodes[pitch_info.pitch_class] = circle
		_pitch_circles_parent_node.add_child(circle, true)
		#circle.visible = false # start off by default
		#circle.position = pitch_info.pos
	self._move_pitch_nodes()
	self._configure_pitch_text_nodes()
	self._configure_pitch_circle_nodes()
	
	# set up rotation arc
	self._rotate_arc.start_angle = self.rotate_arc_start_angle
	self._rotate_arc.end_angle = self.rotate_arc_end_angle
	self._rotate_arc.color = self.rotate_arc_color


#region animations

## Given structured information about the song, create a list of animations to play at set times.
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep]:
	print_verbose("hrmn_animate(): start")
	var animations: Array[Utils.AnimationStep] = []

	# animate key changes
	print_verbose("hrmn_animate(): animating key changes")
	var keys: Array[Dictionary] = Array(Utils.as_array(music_data["keys"]), TYPE_DICTIONARY, "", null)
	animations.append_array(animate_key_changes(keys))

	# animate chord roots
	print_verbose("hrmn_animate(): animating chord roots")
	var chord_roots: Array[Dictionary] = Array(Utils.as_array(music_data["chord_roots"]), TYPE_DICTIONARY, "", null)
	animations.append_array(animate_chord_roots(chord_roots))

	# TODO: animate notes played
	
	print_verbose("hrmn_animate(): end")
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
		if selected_pitches.size() > num_pitch_circles_selectable:
			selected_pitches.pop_back()
		# create a new pitch_circle_colors for this new selection
		var new_pitch_circle_colors: Array[Color] = Array(Utils.fill_array(12, Color.TRANSPARENT), TYPE_COLOR, "", null)
		var selected_indexes_to_set := range(selected_pitches.size())
		selected_indexes_to_set.reverse()
		for i: int in selected_indexes_to_set:
			var pitch_class := selected_pitches[i]
			var color := Color.WHITE
			color.a =  pitch_circle_history_alpha_decay_factor ** i
			new_pitch_circle_colors[pitch_class] = color
		anims.append(Utils.AnimationStep.new(self, time - .05, time + .05, [Utils.PropertyChange.new("pitch_circle_colors", previous_pitch_circle_colors, new_pitch_circle_colors)]))

		# update tracking vars for next iteration
		previous_selected_pitch_class = new_pitch_class
		previous_pitch_circle_colors = new_pitch_circle_colors

	print_verbose("animate_chord_roots(): end")
	return anims


func animate_key_changes(keys: Array[Dictionary]) -> Array[Utils.AnimationStep]:
	print_verbose("animate_key_changes(): start")
	# build a sequence of rotation animations to play
	var anims: Array[Utils.AnimationStep] = []

	# set initial animation states
	var previous_root_pitch_class: int = keys[0]["elem"]["pitch"]["pitchClass"]
	var previous_rotate_angle: float = _angle_for_pitch_at_top(previous_root_pitch_class)
	var previous_pitch_text_colors: Array[Color] = _compute_pitch_text_colors(
		Array(Utils.as_array(keys[0]["elem"]["pitches"]), TYPE_INT, "", null))

	for key: Dictionary in keys.slice(1):

		# make a list of property changes for this key change
		var key_change_anims: Array[Utils.PropertyChange] = []
		# figure out start and end time for the main key change animation
		var target_end_time: float = key["time"]
		var start_time := target_end_time - transition_time

		# detect if root changed
		var root_pitch_class: int = key["elem"]["pitch"]["pitchClass"]
		if key["elem"]["quality"] == "minor":
			root_pitch_class = (root_pitch_class + 3) % 12
		if root_pitch_class != previous_root_pitch_class:
			var new_rotate_angle := _minimize_angle_absolute_diff(
				_angle_for_pitch_at_top(root_pitch_class), previous_rotate_angle)
			# add extra animation of rotate_arc appearing one "transition_time" increment earlier
			anims.append(Utils.AnimationStep.new(self, start_time - transition_time * 1.5, start_time - transition_time * 0.5 - 0.05,
				[Utils.PropertyChange.new("rotate_arc_end_angle", 0.0, previous_rotate_angle - new_rotate_angle)]))
			# in the main key-change animation, add the follow-up step to retract the arc end alongside the rotation
			key_change_anims.append(Utils.PropertyChange.new("rotate_arc_end_angle", previous_rotate_angle - new_rotate_angle, 0.0))
			#key_change_anims.append(Utils.PropertyChange.new("rotate_arc_end_angle", previous_rotate_angle, new_rotate_angle))
			
			# animate circle rotating
			key_change_anims.append(Utils.PropertyChange.new("rotate_angle",
				previous_rotate_angle, new_rotate_angle))
			previous_root_pitch_class = root_pitch_class
			previous_rotate_angle = new_rotate_angle

		# color individual pitches based on key
		var new_pitch_text_colors: Array[Color] = _compute_pitch_text_colors(
			Array(Utils.as_array(key["elem"]["pitches"]), TYPE_INT, "", null))
		if new_pitch_text_colors != previous_pitch_text_colors:
			key_change_anims.append(Utils.PropertyChange.new("pitch_text_colors",
				previous_pitch_text_colors,
				new_pitch_text_colors))
			previous_pitch_text_colors = new_pitch_text_colors

		# if we ended up with any notes to change, add it to the overall list
		if key_change_anims.size() > 0:
			anims.append(Utils.AnimationStep.new(self, start_time, target_end_time, key_change_anims))

	print_verbose("animate_key_changes(): end")
	return anims

func _minimize_angle_absolute_diff(angle: float, target: float=0) -> float:
	print_verbose("_minimize_angle_absolute_diff(): start (angle=%f, target=%f)" % [angle, target])
	if angle - target == PI:
		# TODO: let user decide which way to flip?
		return angle
	while angle - target > PI:
		angle -= TAU
	while angle - target < -PI:
		angle += TAU
	print_verbose("_minimize_angle_absolute_diff(): end (returning angle=%f)" % [angle])
	return angle

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
	

# TODO: rename to animate_rotate_angle
## Testing: Create an animation to rotate the circle
func animate_rotate(angle_start: float, angle_end: float, time_start: float, time_end: float) -> Utils.AnimationStep:
	return Utils.AnimationStep.new(self, time_start, time_end, [Utils.PropertyChange.new("rotate_angle", angle_start, angle_end)])

func animate_rotate_pitch(pitch_start: int, pitch_end: int, time_start: float, time_end: float) -> Utils.AnimationStep:
	return animate_rotate(_angle_for_pitch_at_top(pitch_start), _angle_for_pitch_at_top(pitch_end), time_start, time_end)

#endregion
