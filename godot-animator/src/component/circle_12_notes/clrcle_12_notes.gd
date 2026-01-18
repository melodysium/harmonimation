@tool

class_name Circle12Notes

extends HarmonimationWidget

# TODO: user or animation configure whether to use all/some flats or sharps for non-natural pitches

#region constants and types

## Layout changed, indicating possible need to reposition other components
signal layout_changed

# TODO: make some of these configurable?

## Default time before a new key change when the Circle will start rotating
const DEFAULT_ROTATE_TRANSITION_TIME = 0.3

## Angle (in radians) for one step of twelve around the circle
const ANGLE_PER_STEP := TAU / 12

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
		self.emit_signal("layout_changed")


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
		self.emit_signal("layout_changed")

## First pitch class at the "top" of the node. 0 = C, 1 = Db, ... 11 = B
@export_range(0, 11, 1.0)
var first_pitch_class := 0:
	set(val):
		first_pitch_class = val
		self.emit_signal("layout_changed")

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
		self.emit_signal("layout_changed")

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

## Arc which appears when showing impending rotations
@onready
var _rotate_arc: Arc2D = $RotateArc


#endregion



#region internal state vars

#endregion



#region private helpers


func _angle_for_pitch_at_top(selected_pitch_class: int, previous_angle: float = 0.0) -> float:
	var diff_pitch_classes := first_pitch_class - selected_pitch_class
	var diff_steps := diff_pitch_classes * pitches_per_step
	var new_angle := diff_steps * (ANGLE_PER_STEP)
	new_angle += roundf((new_angle - previous_angle) / TAU) * -TAU
	return new_angle

## get local position at the top of this circle
func _circle_start() -> Vector2:
	return Vector2.UP * self.radius

## all positions around the circle, indexed by pitch_class
func _list_positions(_radius: float = self.radius) -> Array[PitchInfo]:
	var positions: Array[PitchInfo] = []
	for pitch_class: int in range(12):
		var pos := _get_position_for_pitchclass(pitch_class, _radius)
		positions.append(PitchInfo.new(pitch_class, pos))
	print_verbose("_list_positions(). pitches_per_step=%s; first_pitch_class=%s; rotate_angle=%s; positions=%s" % [pitches_per_step, first_pitch_class, rotate_angle, positions])
	return positions


func _get_step_for_pitchclass(pitch_class: int) -> int:
	return (pitch_class - self.first_pitch_class) * self.pitches_per_step % 12


func _get_pitchclass_for_step(step: int) -> int:
	return (step * self.pitches_per_step + self.first_pitch_class) % 12


func _get_position_for_pitchclass(pitch_class: int, _radius: float = self.radius) -> Vector2:
	var step := _get_step_for_pitchclass(pitch_class)
	var angle := ANGLE_PER_STEP * step + self.rotate_angle
	return (Vector2.UP * _radius).rotated(angle)


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

#endregion



func _ready() -> void:
	# set up rotation arc
	self._rotate_arc.start_angle = self.rotate_arc_start_angle
	self._rotate_arc.end_angle = self.rotate_arc_end_angle
	self._rotate_arc.color = self.rotate_arc_color

	## connect animation signals
	#super._connect_signals()


#region animations


## Given structured information about the song, create a list of animations to play at set times.
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep]:
	print_verbose("hrmn_animate(): start")
	var animations: Array[Utils.AnimationStep] = []

	# animate key changes
	print_verbose("hrmn_animate(): animating key changes")
	var keys: Array[Dictionary] = Array(Utils.as_array(music_data["keys"]), TYPE_DICTIONARY, "", null)
	animations.append_array(animate_key_changes(keys))
	
	print_verbose("hrmn_animate(): end")
	return animations


func animate_key_changes(keys: Array[Dictionary]) -> Array[Utils.AnimationStep]:
	print_verbose("animate_key_changes(): start")
	# build a sequence of rotation animations to play
	var anims: Array[Utils.AnimationStep] = []

	# set initial animation states
	var previous_root_pitch_class: int = keys[0]["elem"]["pitch"]["pitchClass"]
	var previous_rotate_angle: float = _angle_for_pitch_at_top(previous_root_pitch_class)
	#var previous_pitch_text_colors: Array[Color] = _compute_pitch_text_colors(
		#Array(Utils.as_array(keys[0]["elem"]["pitches"]), TYPE_INT, "", null))

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
			anims.append(Utils.AnimationStep.new(
				PackedFloat32Array([start_time - transition_time * 1.5, start_time - transition_time * 0.5 - 0.05]),
				{self: [Utils.PropertyChange.pair("rotate_arc_end_angle", 0.0, previous_rotate_angle - new_rotate_angle)]}))
			# in the main key-change animation, add the follow-up step to retract the arc end alongside the rotation
			key_change_anims.append(Utils.PropertyChange.pair("rotate_arc_end_angle", previous_rotate_angle - new_rotate_angle, 0.0))
			#key_change_anims.append(Utils.PropertyChange.new("rotate_arc_end_angle", previous_rotate_angle, new_rotate_angle))
			
			# animate circle rotating
			key_change_anims.append(Utils.PropertyChange.pair("rotate_angle",
				previous_rotate_angle, new_rotate_angle))
			previous_root_pitch_class = root_pitch_class
			previous_rotate_angle = new_rotate_angle

		# if we ended up with any notes to change, add it to the overall list
		if key_change_anims.size() > 0:
			anims.append(Utils.AnimationStep.new(
				PackedFloat32Array([start_time, target_end_time]),
				{self: key_change_anims}))

	print_verbose("animate_key_changes(): end")
	return anims


# TODO: rename to animate_rotate_angle
## Testing: Create an animation to rotate the circle
func animate_rotate(angle_start: float, angle_end: float, time_start: float, time_end: float) -> Utils.AnimationStep:
	return Utils.AnimationStep.new(
		PackedFloat32Array([time_start, time_end]),
		{self: [Utils.PropertyChange.pair("rotate_angle", angle_start, angle_end)]})

func animate_rotate_pitch(pitch_start: int, pitch_end: int, time_start: float, time_end: float) -> Utils.AnimationStep:
	return animate_rotate(_angle_for_pitch_at_top(pitch_start), _angle_for_pitch_at_top(pitch_end), time_start, time_end)

#endregion
