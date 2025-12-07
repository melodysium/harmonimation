@tool

extends Node2D

@export var dummy: NodePath

@onready var animation_player: AnimationPlayer = $HarmonimationPlayer
@onready var circle_12_notes: Circle12Notes = $Clrcle12Notes

func _ready() -> void:
	#print(animation_player.get_animation("play_music_circle"))
	
	## TODO: REMOVE. testing: call animate
	if animation_player != null:
		var animation := Utils.setup_animation(animation_player)
		#Utils.apply_animation(circle_12_notes.animate_rotate(0, PI / 3, 2, 3), animation_player, animation)
		
		for anim in circle_12_notes.animate_on_data(Utils.MUSIC_DATA):
			Utils.apply_animation(anim, animation_player, animation)
