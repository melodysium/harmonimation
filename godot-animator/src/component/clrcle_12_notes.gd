@tool

extends Node2D

## Radius for main circle / pitch names 
@export_range(0, 100, 1.0, "or_greater") var radius := 50.0:
	set(val):
		assert(_background_circle_node != null)
		_background_circle_node.radius = val
		radius = val
# TODO: eliminate this, just use Godot native object scaling


## Number of steps between each pitch
@export_range(1, 11, 1.0) var pitches_per_step := 1

@export_group("internal links")
## Background ring underneath pitches
@export var _background_circle_node: Circle2D
## Parent node for dynamically-added pitch text
@export var _pitch_text_parent_node: Node2D
## Parent node for dynamically-added pitch circles
@export var _pitch_circles_parent_node: Node2D

const BASE_PITCH_NAME_FONT_SIZE := 12
const BASE_PITCH_CIRCLE_RADIUS := 0.2

class PitchInfo:
	var pitch_class: int
	var pos: Vector2
	
	func _init(pitch_class: int, pos: Vector2) -> void:
		self.pitch_class = pitch_class
		self.pos = pos

var circle_start := Vector2.UP * radius
const ONE_STEP_ANGLE := TAU / 12

func _list_positions() -> Array[PitchInfo]:
	var positions: Array[PitchInfo] = []
	print("pitches_per_step=%s" % pitches_per_step)
	for i: int in range(12):
		var step := (i * pitches_per_step) % 12
		print("step=%s" % step)
		#print("transform=%s" % transform)
		var pos := circle_start.rotated(ONE_STEP_ANGLE * i)
		positions.append(PitchInfo.new(step, pos))
	return positions



func _ready() -> void:

	# Construct child nodes
	for pitch_info: PitchInfo in _list_positions():
		
		# Pitch text
		var pitch_name = Utils.Pitch.pitchclass_to_pitchname(pitch_info.pitch_class)
		var text = Text2D.new(
			Utils.DEFAULT_FONT,
			pitch_name,
			HORIZONTAL_ALIGNMENT_CENTER,
			VERTICAL_ALIGNMENT_CENTER,
			5000,
			BASE_PITCH_NAME_FONT_SIZE
		)
		_pitch_text_parent_node.add_child(text, true) # TODO: disable force_readable_name
		text.position = pitch_info.pos
		#print("PitchInfo(pitch_class=%s, pos=%s)" % [pitch_info.pitch_class, pitch_info.pos])
		#print("text.global_position=%s" % text.global_position)
		
		# Pitch circle
		var circle = Circle2D.new(
			self.radius * BASE_PITCH_CIRCLE_RADIUS,
			Color.WHITE,
			false,
			self.radius * .02
		)
		_pitch_circles_parent_node.add_child(circle, true)
		circle.position = pitch_info.pos
		circle.visible = false # start off by default
