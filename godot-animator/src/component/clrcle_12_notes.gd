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
		assert(_background_circle_node != null)
		_background_circle_node.radius = val
		radius = val
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

## Time before a new key change when the Circle will start rotating
@export_range(0.0, 2.0, 0.01, "or_greater")
var transition_time := DEFAULT_ROTATE_TRANSITION_TIME


#endregion


#region animation primitives

#@export_group("Raw Animation Primitives")

## Rotate angle (keeps note text oriented upwards)
#@export_range(-TAU, TAU, 0.01, "or_less", "or_greater")
var rotate_angle := 0.0:
	set(val):
		# if < 0 or >= TAU (radians), cycle back within that range
		if val <= -TAU or val >= TAU:
			print_verbose("trying to wrap, should come out as %f" % fmod(val, TAU))
			val = fmod(val, TAU)
		rotate_angle = val
		_move_pitch_nodes()

## Colors used for pitch highlight circles. Start transparent.
#@export
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
	for i in range(12):
		_pitch_text_nodes[i].text = Utils.Pitch.pitchclass_to_pitchname(i)

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
			BASE_PITCH_NAME_FONT_SIZE
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


#region animations

## Given structured information about the song, create a list of animations to play at set times.
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep]:
	var animations: Array[Utils.AnimationStep] = []

	# animate key changes
	var keys: Array[Dictionary] = Array(music_data["keys"], TYPE_DICTIONARY, "", null) # TODO: handle warning?
	animations.append_array(animate_key_changes(keys))

	# TODO: animate pitch selections (i.e. chords)
	var chord_roots: Array[Dictionary] = Array(music_data["chord_roots"], TYPE_DICTIONARY, "", null) # TODO: handle warning?
	animations.append_array(animate_chord_roots(chord_roots))

	# TODO: animate notes played

	return animations

func animate_chord_roots(chord_roots: Array[Dictionary]) -> Array[Utils.AnimationStep]:
	var anims: Array[Utils.AnimationStep] = []

	var previous_pitch_circle_colors := pitch_circle_colors
	var previous_selected_pitch_class := -1 # -1 = none, 0-11 = selected

	for chord_root: Dictionary in chord_roots:
		var time: float = chord_root["time"]
		var new_pitch_class: int = chord_root["elem"]["pitchClass"]

		if new_pitch_class == previous_selected_pitch_class:
			# same pitch, no need to animate
			continue

		# create a clone of pitch_circle_colors for this new selection
		var new_pitch_circle_colors: Array[Color] = []
		for i in range(12):
			if i == new_pitch_class:
				new_pitch_circle_colors.append(Color.WHITE)
			#elif i == previous_selected_pitch_class:
				#new_pitch_circle_colors.append(Color.TRANSPARENT)
			else:
				new_pitch_circle_colors.append(Color.TRANSPARENT)
		anims.append(Utils.AnimationStep.new(self, time - .05, time + .05, [Utils.PropertyChange.new("pitch_circle_colors", previous_pitch_circle_colors, new_pitch_circle_colors)]))

		# update tracking vars for next iteration
		previous_selected_pitch_class = new_pitch_class
		previous_pitch_circle_colors = new_pitch_circle_colors

	return anims


func animate_key_changes(keys: Array[Dictionary]) -> Array[Utils.AnimationStep]:
	# build a sequence of rotation animations to play
	var anims: Array[Utils.AnimationStep] = []

	# pull out info from music_data we care about
	var previous_root_pitch_class: int = keys[0]["elem"]["pitch"]["pitchClass"]

	# TODO: color pitches based on what is in-key
	# previous_pitches_in_key: dict[int, bool] = {
	# 	pitch_idx: pitch_idx
	# 	in set(p.pitchClass for p in music_data.keys[0].elem.getPitches())
	# 	for _, pitch_idx in circle12._list_steps()
	# }

	for key: Dictionary in keys.slice(1):

		# make a list of property changes for this key change
		var key_change_anims: Array[Utils.PropertyChange] = []

		# get info about new key
		# pitchesInKey = set(p.pitchClass for p in key.getPitches())
		# figure out which pitch to use for root
		var root_pitch_class: int = key["elem"]["pitch"]["pitchClass"]

		# if root changed, animate circle rotating
		if root_pitch_class != previous_root_pitch_class:
			key_change_anims.append(Utils.PropertyChange.new("rotate_angle",
				_angle_for_pitch_at_top(previous_root_pitch_class),
				_angle_for_pitch_at_top(root_pitch_class)))

		# TODO: animate any individual pitches needing to change highlighting
		# TODO: this will require adding data in music_data.json: pitches_in_key
		# pitches_in_new_key = {
		#     pitch_idx: pitch_idx in pitchesInKey
		#     for _, pitch_idx in circle12._list_steps()
		# }
		# for pitch_idx, pitch_is_in_new_key in pitches_in_new_key.items():
		#     # optimization: skip animation for this pitch if not changed from last key
		#     if previous_pitches_in_key[pitch_idx] == pitch_is_in_new_key:
		#         continue

		#     # this pitch needs to animate
		#     final_color = DEFAULT_NOTE_IN_KEY_COLOR if pitch_is_in_new_key else DEFAULT_NOTE_NOT_IN_KEY_COLOR
		#     key_change_anims.append(
		#             AnimateProperty(circle12.get_pitch_text(pitch_idx), 'color', final_color)
		#         )

		# done processing this key change
		previous_root_pitch_class = root_pitch_class
		# previous_pitches_in_key = pitches_in_new_key

		# if we ended up with any notes to change, add it to the overall list
		if key_change_anims.size() > 0:
			var target_end_time: float = key["time"]
			var start_time := target_end_time - transition_time
			anims.append(Utils.AnimationStep.new(self, start_time, target_end_time, key_change_anims))

	return anims

# TODO: rename to animate_rotate_angle
## Testing: Create an animation to rotate the circle
func animate_rotate(angle_start: float, angle_end: float, time_start: float, time_end: float) -> Utils.AnimationStep:
	return Utils.AnimationStep.new(self, time_start, time_end, [Utils.PropertyChange.new("rotate_angle", angle_start, angle_end)])

func animate_rotate_pitch(pitch_start: int, pitch_end: int, time_start: float, time_end: float) -> Utils.AnimationStep:
	return animate_rotate(_angle_for_pitch_at_top(pitch_start), _angle_for_pitch_at_top(pitch_end), time_start, time_end)

#endregion
