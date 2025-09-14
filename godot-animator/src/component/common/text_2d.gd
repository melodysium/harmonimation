@tool

extends Node2D

const ORIGIN := Vector2(0, 0)

@export var font := ThemeDB.fallback_font:
	set(val):
		font = val
		queue_redraw()
@export var text := "placeholder":
	set(val):
		text = val
		queue_redraw()
@export var alignment := HORIZONTAL_ALIGNMENT_LEFT:
	set(val):
		alignment = val
		queue_redraw()
@export_range(-1, 100, 1.0, "or_greater") var width := -1:
	set(val):
		width = val
		queue_redraw()
@export_range(0, 100, 1.0, "or_greater") var font_size := 16:
	set(val):
		font_size = val
		queue_redraw()
# TODO: others: max_lines, modulate, brk_flags, justification_flags, direction, orientation


func _draw() -> void:
	draw_multiline_string(font, ORIGIN, text, alignment, width, font_size)
