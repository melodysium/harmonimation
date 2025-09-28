@tool

class_name Circle12Notes

extends Node2D

## TODO: make these configurable?
## Font size for pitch names
const BASE_PITCH_NAME_FONT_SIZE := 12
## Circle radius for pitch circles
const BASE_PITCH_CIRCLE_RADIUS := 0.2

@export_group("setup options")

## Radius for main circle / pitch names
@export_range(0, 100, 1.0, "or_greater") var radius := 50.0:
	set(val):
		assert(_background_circle_node != null)
		_background_circle_node.radius = val
		radius = val
		_move_pitch_nodes()


## Number of steps between each pitch
@export_range(1, 11, 1.0) var pitches_per_step := 1:
	set(val):
		if ![1, 5, 7, 11].has(val):
			Utils.print_err("WARNING: Circle12Notes currently only supports pitches_per_step values of [1, 5, 7, 11], but you picked: %s. Ignoring." % val)
			return
		pitches_per_step = val
		_move_pitch_nodes()

## First pitch class at the "top" of the node. 0 = C, 1 = Db, ... 11 = B
@export_range(0, 11, 1.0) var first_pitch_class := 0:
	set(val):
		first_pitch_class = val
		_move_pitch_nodes()


@export_group("animation controls")

## Rotate angle (keeps note text oriented upwards)
@export_range(-TAU, TAU, 0.01, "or_less", "or_greater") var rotate_angle := 0.0:
	set(val):
		# if < 0 or >= TAU (radians), cycle back within that range
		if val <= -TAU or val >= TAU:
			print_verbose("trying to wrap, should come out as %f" % fmod(val, TAU))
			val = fmod(val, TAU)
		rotate_angle = val
		_move_pitch_nodes()

## Colors used for pitch highlight circles. Start transparent.
@export var pitch_circle_colors: Array[Color] = Array(Utils.fill_array(12, Color.TRANSPARENT), TYPE_COLOR, "", null):
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

## Background ring underneath pitches
@onready var _background_circle_node : Circle2D = $BackgroundCircle
## Parent node for dynamically-added pitch text
@onready var _pitch_text_parent_node : Node2D = $PitchText
## Parent node for dynamically-added pitch circles
@onready var _pitch_circles_parent_node : Node2D = $PitchCircles


## Mapping of pitch_class to pitch labels
var _pitch_text_nodes: Dictionary[int, Text2D] = {}

## Mapping of pitch_class to pitch labels
var _pitch_circle_nodes: Dictionary[int, Circle2D] = {}

class PitchInfo:
	var pitch_class: int
	var pos: Vector2

	func _init(pitch_class: int, pos: Vector2) -> void:
		self.pitch_class = pitch_class
		self.pos = pos

	func _to_string() -> String:
		return "PitchInfo[pcls=%s, pos=%s]" % [self.pitch_class, self.pos]

const ONE_STEP_ANGLE := TAU / 12

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


## Given structured information about the song, create a list of animations to play at set times.
#func animate_on_data(music_data: Dictionary) -> Array[Utils.AnimationStep]
	#return [];

## Testing: Create an animation to rotate the circle
func animate_rotate(angle_start: float, angle_end: float, time_start: float, time_end: float) -> Utils.AnimationStep:
	return Utils.AnimationStep.new(self, time_start, time_end, [Utils.PropertyChange.new("rotate_angle", angle_start, angle_end)])
