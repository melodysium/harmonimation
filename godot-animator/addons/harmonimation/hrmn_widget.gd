@tool

@abstract
class_name HarmonimationWidget
extends Node


## Given data about a piece of music, determine all of the animation steps to apply
@abstract
func hrmn_animate(music_data: Dictionary) -> Array[Utils.AnimationStep];

#region signal interface, removed now

### Reference to the HrmnRenderer node
#@onready
#var hrmn_renderer: HarmonimationRenderer = (func() -> HarmonimationRenderer:
	#var parent = self.get_parent()
	#while parent != null and parent is not HarmonimationRenderer:
		#parent = parent.get_parent()
	#assert(parent != null, "%s %s: requires some parent to be a HarmonimationRenderer" % [self.get_class(), self.name])
	#return parent
	#).call()
#
#
#
### Call in each child class to trigger animations whenever signaled
#func _connect_signals() -> void:
	#assert(hrmn_renderer != null, "%s %s cannot _connect_signals if no HarmonimationRenderer parent found" % [self.get_class(), self.name])
	#hrmn_renderer.compute_animations.connect(_handle_compute_animations)
#
#
### Handle trigger signal, return animations via return signal
#func _handle_compute_animations(music_data: Dictionary) -> void:
	#assert(hrmn_renderer != null, "%s %s cannot _handle_compute_animations if no HarmonimationRenderer parent found" % [self.get_class(), self.name])
	#var anims = hrmn_animate(music_data)
	#hrmn_renderer.animations_computed.emit(anims)

#endregion
