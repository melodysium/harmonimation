@tool

class_name Circle2D

extends Node2D

const ORIGIN := Vector2(0, 0)

@export_range(0, 100, 1.0, "or_greater") var radius := 10.0:
	set(val):
		radius = val
		queue_redraw()
@export var color := Color.WHITE:
	set(val):
		color = val
		queue_redraw()
@export var filled := true:
	set(val):
		filled = val
		queue_redraw()
@export_range(0, 10, 0.01, "or_greater") var width := 0.0:
	set(val):
		width = val
		if not filled:
			queue_redraw()
@export var antialiased := false:
	set(val):
		antialiased = val
		queue_redraw()

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
