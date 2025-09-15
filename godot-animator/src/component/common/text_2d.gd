@tool

class_name Text2D

extends Node2D

const ORIGIN := Vector2(0, 0)

@export var font_vertical_ratio := 2.5: # HACK: determined empirically for a default font, do not trust it. may need to fix for different fonts in the future.
	set(val):
		font_vertical_ratio = val
		queue_redraw()

var DEFAULT_FONT := Utils.DEFAULT_FONT
@export var font := DEFAULT_FONT:
	set(val):
		font = val
		queue_redraw()

const DEFAULT_TEXT := "placeholder"
@export var text := DEFAULT_TEXT:
	set(val):
		text = val
		queue_redraw()

const DEFAULT_H_ALIGNMENT := HORIZONTAL_ALIGNMENT_LEFT
@export var h_alignment := DEFAULT_H_ALIGNMENT:
	set(val):
		h_alignment = val
		queue_redraw()

const DEFAULT_V_ALIGNMENT := VERTICAL_ALIGNMENT_BOTTOM
@export var v_alignment := DEFAULT_V_ALIGNMENT:
	set(val):
		v_alignment = val
		queue_redraw()

const DEFAULT_WIDTH := 5000
@export_range(-1, 100, 1.0, "or_greater") var width := DEFAULT_WIDTH:
	set(val):
		width = val
		queue_redraw()

const DEFAULT_FONT_SIZE := 16
@export_range(0.0, 100, 1.0, "or_greater") var font_size := DEFAULT_FONT_SIZE:
	set(val):
		font_size = val
		queue_redraw()
# TODO: others: max_lines, modulate, brk_flags, justification_flags, direction, orientation


func _init(
		font := DEFAULT_FONT,
		text := DEFAULT_TEXT, 
		h_alignment := DEFAULT_H_ALIGNMENT,
		v_alignment := DEFAULT_V_ALIGNMENT,
		width := DEFAULT_WIDTH,
		font_size := DEFAULT_FONT_SIZE,
	) -> void:
	self.font = font
	self.text = text
	self.h_alignment = h_alignment
	self.v_alignment = v_alignment
	self.width = width
	self.font_size = font_size


func _draw() -> void:
	
	# HACK: offset draw position to center of node based on alignment
	var h_draw_offset := 0.0
	var v_draw_offset := 0.0
	if h_alignment == HORIZONTAL_ALIGNMENT_CENTER:
		h_draw_offset = -width/2
	if v_alignment == VERTICAL_ALIGNMENT_CENTER:
		v_draw_offset = font_size/font_vertical_ratio
		#print("v_draw_offset=%s" % v_draw_offset)
	elif v_alignment == VERTICAL_ALIGNMENT_BOTTOM:
		pass # default behavior
	else:
		assert(false, "vertial alignments other than CENTER and BOTTOM not yet implemented")
	draw_set_transform(Vector2(h_draw_offset, v_draw_offset))
	
	# Draw the actual text, woa!
	draw_string(font, ORIGIN, text, h_alignment, width, font_size)
	#draw_multiline_string(font, ORIGIN, text, h_alignment, width, font_size)
