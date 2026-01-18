@tool

extends HarmonimationWidget


## Given data about a piece of music, determine all of the animation steps to apply
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep]:
	return get_parent().hrmn_animate(music_data)
