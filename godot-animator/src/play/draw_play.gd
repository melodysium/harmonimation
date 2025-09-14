@tool

extends Node2D

# following tutorial:
# https://docs.godotengine.org/en/stable/tutorials/2d/custom_drawing_in_2d.html

var default_font : Font = ThemeDB.fallback_font;

@onready var head : PackedVector2Array = float_array_to_Vector2Array(coords_head)
@onready var mouth : PackedVector2Array = float_array_to_Vector2Array(coords_mouth)
@export var _mouth_width : float = 4.4 :
	set(value):
		_mouth_width = value
		queue_redraw()
var _max_width : float = 7
var _time : float = 0

@export var rotation_speed : float = 1  # In radians per second.

@export var foo : int = 0:
	set(value):
		foo = value

const coords_head : Array[Array] = [
	[ 22.952, 83.271 ],  [ 28.385, 98.623 ],
	[ 53.168, 107.647 ], [ 72.998, 107.647 ],
	[ 99.546, 98.623 ],  [ 105.048, 83.271 ],
	[ 105.029, 55.237 ], [ 110.740, 47.082 ],
	[ 102.364, 36.104 ], [ 94.050, 40.940 ],
	[ 85.189, 34.445 ],  [ 85.963, 24.194 ],
	[ 73.507, 19.930 ],  [ 68.883, 28.936 ],
	[ 59.118, 28.936 ],  [ 54.494, 19.930 ],
	[ 42.039, 24.194 ],  [ 42.814, 34.445 ],
	[ 33.951, 40.940 ],  [ 25.637, 36.104 ],
	[ 17.262, 47.082 ],  [ 22.973, 55.237 ]
]

const coords_mouth : Array[Array] = [
	[ 22.817, 81.100 ], [ 38.522, 82.740 ],
	[ 39.001, 90.887 ], [ 54.465, 92.204 ],
	[ 55.641, 84.260 ], [ 72.418, 84.177 ],
	[ 73.629, 92.158 ], [ 88.895, 90.923 ],
	[ 89.556, 82.673 ], [ 105.005, 81.100 ]
]

static func float_array_to_Vector2Array(coords : Array[Array]) -> PackedVector2Array:
	# Convert the array of floats into a PackedVector2Array.
	var array : PackedVector2Array = []
	for coord: Array[float] in coords:
		array.append(Vector2(coord[0], coord[1]))
	return array


func _ready():
	foo = 5
	rotation = 0


func _process(delta: float):
	_time += delta
	_mouth_width = abs(sin(_time) * _max_width)
	#rotation -= rotation_speed * delta
	#position = Vector2(60, 60)
	


func _draw():
	draw_set_transform(Vector2(-64.273, -67.4565))
	#if not is_node_ready():
		#await ready

	# We will use white to draw the line.
	var white : Color = Color.WHITE
	var godot_blue : Color = Color("478cbf")
	var grey : Color = Color("414042")

	# Face shape
	draw_polygon(head, [ godot_blue ])
	# Mout
	draw_polyline(mouth, white, _mouth_width)

	# Four circles for the 2 eyes: 2 white, 2 grey.
	draw_circle(Vector2(42.479, 65.4825), 9.3905, white)
	draw_circle(Vector2(85.524, 65.4825), 9.3905, white)
	draw_circle(Vector2(43.423, 65.92), 6.246, grey)
	draw_circle(Vector2(84.626, 66.008), 6.246, grey)

	# Draw a short but thick white vertical line for the nose.
	draw_line(Vector2(64.273, 60.564), Vector2(64.273, 74.349), white, 5.8)
	
	# Draw GODOT text below the logo with the default font, size 22.
	draw_string(default_font, Vector2(20, 130), "GODOT",
				HORIZONTAL_ALIGNMENT_CENTER, 90, 22)
	#draw_string_outline(default_font, Vector2(20, 130), "GODOT",
				#HORIZONTAL_ALIGNMENT_CENTER, 90, 22, 5) # size param just applies to adding more outline; font would have to set transparent in its properties somewhere to have *just* outline
