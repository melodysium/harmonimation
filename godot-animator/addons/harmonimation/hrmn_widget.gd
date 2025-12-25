@tool

@abstract
class_name HarmonimationWidget
extends Node

@abstract
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep];

## Call in each child class to trigger animations whenever signaled
func _connect_signals() -> void:
	HrmnSignalBus.compute_animations.connect(_handle_compute_animations)

## Handle trigger signal, return animations via return signal
func _handle_compute_animations(music_data: Dictionary) -> void:
	var anims = hrmn_animate(music_data)
	HrmnSignalBus.animations_computed.emit(anims)
