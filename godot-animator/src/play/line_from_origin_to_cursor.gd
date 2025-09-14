extends Node2D

const ORIGIN : Vector2 = Vector2(0, 0)
@export var width : int = 10
@export var color : Color = Color.GREEN
@export_range(1, 1000) var segments : int = 100
@export var antialiasing : bool = false

## User's mouse position
var pos_mouse : Vector2

func _process(_delta: float):
	var mouse_position := get_viewport().get_mouse_position()
	if mouse_position != pos_mouse:
		pos_mouse = mouse_position
		queue_redraw()

func _draw():
	# Average points to get center.
	var center := ORIGIN.lerp(pos_mouse, 0.5)
	# Calculate the rest of the arc parameters.
	var radius : float = ORIGIN.distance_to(pos_mouse) / 2
	var start_angle : float = (pos_mouse - ORIGIN).angle()
	var end_angle : float = (ORIGIN - pos_mouse).angle()
	while end_angle < 0:  # end_angle is likely negative, normalize it.
		end_angle += TAU
		
	# Draw the center point as a circle
	draw_circle(center, 5, Color.BLUE)

	# Finally, draw the arc.
	draw_arc(center, radius, start_angle, end_angle, segments, color,
			 width, antialiasing)
