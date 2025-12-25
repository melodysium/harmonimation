@tool

extends Node2D

@export var dummy: NodePath
@export var json: MusicScoreData
@export var pic: RectangleShape2D

@onready var animation_player: AnimationPlayer = $HarmonimationPlayer
@onready var circle_12_notes: Circle12Notes = $Circle12Notes

func _ready() -> void:
	#print(animation_player.get_animation("play_music_circle"))

	# TODO: REMOVE. testing: call animate
	if animation_player != null:
		var animation := Utils.setup_animation(animation_player)
		#Utils.apply_animation(circle_12_notes.animate_rotate(0, PI / 3, 2, 3), animation_player, animation)
		
		for anim in circle_12_notes.hrmn_animate(Utils.MUSIC_DATA):
			Utils.apply_animation(anim, animation_player, animation)

	pass
