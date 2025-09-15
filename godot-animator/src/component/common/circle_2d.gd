@tool

class_name Circle2D

extends Node2D

const ORIGIN := Vector2(0, 0)

const DEFAULT_RADIUS := 10.0
@export_range(0, 100, 1.0, "or_greater") var radius := DEFAULT_RADIUS:
	set(val):
		radius = val
		queue_redraw()

const DEFAULT_COLOR := Color.WHITE
@export var color := DEFAULT_COLOR:
	set(val):
		color = val
		queue_redraw()

const DEFAULT_FILLED := true
@export var filled := DEFAULT_FILLED:
	set(val):
		filled = val
		queue_redraw()

const DEFAULT_WIDTH := 0.0
@export_range(0, 10, 0.01, "or_greater") var width := DEFAULT_WIDTH:
	set(val):
		width = val
		if not filled:
			queue_redraw()

const DEFAULT_ANTIALIASED := false
@export var antialiased := DEFAULT_ANTIALIASED:
	set(val):
		antialiased = val
		queue_redraw()


func _init(
		radius := DEFAULT_RADIUS,
		color := DEFAULT_COLOR,
		filled := DEFAULT_FILLED,
		width := DEFAULT_WIDTH,
		antialiased := DEFAULT_ANTIALIASED,
	) -> void:
	self.radius = radius
	self.color = color
	self.filled = filled
	self.width = width
	self.antialiased = antialiased


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
	draw_circle(ORIGIN, radius, color, filled, width, antialiased)
