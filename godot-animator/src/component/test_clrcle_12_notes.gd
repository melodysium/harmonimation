extends Node2D

@onready var animation_player: AnimationPlayer = $Clrcle12Notes/AnimationPlayer
@onready var circle_12_notes: Circle12Notes = $Clrcle12Notes

func _ready() -> void:
	print(animation_player.get_animation("play_music_circle"))
	
	# TODO: REMOVE. testing: call animate
	if animation_player != null:
		Utils.apply_animation(circle_12_notes.animate_rotate(0, PI / 3, 2, 3), animation_player)
