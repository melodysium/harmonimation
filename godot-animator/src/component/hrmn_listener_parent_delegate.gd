@tool

extends HarmonimationWidget


## Given data about a piece of music, determine all of the animation steps to apply
## Full return type: Dictionary[Node, Dictionary[String(property), Array[Keyframe]]
func hrmn_animate(music_data: Dictionary) -> Dictionary[Node, Dictionary]:
	return get_parent().hrmn_animate(music_data)
