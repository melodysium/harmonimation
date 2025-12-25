@tool

extends Node

## Given structured information about the song(music_data: Dictionary):, create a list of animations to play at set times
signal compute_animations

## After a compute_animations signal, Return a list of animations to apply(anims: Array[Utils.AnimationStep])
signal animations_computed

# TODO: define a "animate_config_changed" signal, then call animate_widget when any widget emits it
