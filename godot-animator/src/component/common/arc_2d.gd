@tool

class_name Arc2D

extends Node2D

const ORIGIN := Vector2(0, 0)

## Factor used to determine how many points to draw. Decrease for performance; increase for more smooth arc
const POINT_COUNT_SCALING_FACTOR := 3

const DEFAULT_RADIUS := 10.0
@export_range(0, 100, 1.0, "or_greater") var radius := DEFAULT_RADIUS:
	set(val):
		radius = val
		queue_redraw()

const DEFAULT_START_ANGLE := 0.0
@export_range(0, TAU, 0.01, "or_less", "or_greater")
var start_angle := DEFAULT_START_ANGLE:
	set(val):
		start_angle = val
		queue_redraw()

const DEFAULT_END_ANGLE := TAU / 4
@export_range(0, TAU, 0.01, "or_less", "or_greater")
var end_angle := DEFAULT_END_ANGLE:
	set(val):
		end_angle = val
		queue_redraw()

const DEFAULT_COLOR := Color.WHITE
@export var color := DEFAULT_COLOR:
	set(val):
		color = val
		queue_redraw()

#const DEFAULT_FILLED := true
#@export var filled := DEFAULT_FILLED:
	#set(val):
		#filled = val
		#queue_redraw()

const DEFAULT_WIDTH := 1.0
@export_range(-1, 10, 0.01, "or_greater") var width := DEFAULT_WIDTH:
	set(val):
		width = val
		queue_redraw()

const DEFAULT_ANTIALIASED := false
@export var antialiased := DEFAULT_ANTIALIASED:
	set(val):
		antialiased = val
		queue_redraw()


func _init(
		_radius := DEFAULT_RADIUS,
		_start_angle := DEFAULT_START_ANGLE,
		_end_angle := DEFAULT_END_ANGLE,
		_color := DEFAULT_COLOR,
		_width := DEFAULT_WIDTH,
		_antialiased := DEFAULT_ANTIALIASED,
	) -> void:
	self.radius = _radius
	self.start_angle = _start_angle
	self.end_angle = _end_angle
	self.color = _color
	self.width = _width
	self.antialiased = _antialiased


#var _script_vars: Array = get_script().get_script_property_list().map(func(prop_dict: Dictionary): return prop_dict.name)


#func _ready() -> void:
	#print(get_property_list())
	#var thisScript: GDScript = get_script()
	#print('Properties of "%s":' % [ thisScript.resource_path ])
	#for propertyInfo: Dictionary in thisScript.get_script_property_list():
		#var propertyName: String = propertyInfo.name
		#var propertyValue = get(propertyName)
		#
		#print(' %s = %s' % [ propertyName, propertyValue ])
	#print(_script_vars)

#func _set(property: StringName, value: Variant) -> bool:
	## NOTE: this doesn't do what I want because _set() is only triggered on set() calls in code, not any prop modification.
	#print("_set(%s, %s)" % [property, value])
	#if property in _script_vars:
		#print("queue redraw")
		#set(property, value)
		#queue_redraw()
		#return true
	#return false

func _draw() -> void:
	var point_count := int(absf(start_angle - end_angle) * radius * POINT_COUNT_SCALING_FACTOR)
	if point_count < 2:
		#print_verbose("Arc2D._draw(): point_count < 2. skipping _draw! (start_angle=%f, end_angle=%f, radius=%f, POINT_COUNT_SCALING_FACTOR=%f)" % [start_angle, end_angle, radius, POINT_COUNT_SCALING_FACTOR])
		return
	draw_arc(ORIGIN, radius, start_angle, end_angle, point_count, color, width, antialiased)
