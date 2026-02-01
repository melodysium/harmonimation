@tool

class_name C12NVoiceConnector
extends HarmonimationWidget

# TODO: fancy animations like: jump (from origin to dest), fade in, etc

#region types and consts


#endregion


#region User Config


#endregion


#region Animation Primitives

# TODO: replace with editing the nodes themselves
## Minimal line state controlled by animation player. "Newest" line at the front.
#var line_states: Array[LineState] = []:
	#set(val):
		## TODO: why does this print statement never seem to trigger?
		## NOTE: answer:
		##   1) the LineState type annotation is just dropping any attempted calls
		##   2) the values in such an array are just coming out as <null>
		## NOTE: solution: switch from "Array[State]" animated properties to just directly animating the properties on any created nodes
		## TODO: for later: make some "AnimatedNodeFactory" which accepts tickets, does the actual node creation (pooling when a node can be reused)
		#print("line_states setter called with val=%s" % [val])
		#line_states = val
		##_update_lines()


#endregion


#region Internal state

## Parent node expected to be C12nVoice. Will be null otherwise.
var _voice: C12NVoice

var _c12n: Circle12Notes:
	get():
		if _voice == null:
			printerr("C12NVoiceConnector._c12n: tried to get, but _c12n is null!")
			return null;
		return _voice._c12n
	set(val):
		printerr("C12NVoiceConnector._c12n is a convenience getter, not a variable to set!")

## List of line objects. created in animate_chord_roots
var _lines: Array[LineState] = []

#endregion


func _enter_tree() -> void:
	var parent := get_parent()
	if parent is not C12NVoice:
		printerr("C12NVoiceConnector expects to be a child of a C12NVoice node, but instead this is child of a {} node called {}" % [typeof(parent), parent.name])
		return
	_voice = parent

func _ready() -> void:
	# re-compute layout whenever necessary
	_c12n.connect("layout_changed", _update_lines)
	
	## connect animation signals
	#super._connect_signals()
	pass


#region Private helpers

func _update_lines() -> void:
	if not is_node_ready():
		return
	#print("C12NVoiceConnectors._update_lines(): start. _lines = %s" % [_lines])
	for i in range(_lines.size()):
		_position_line(_lines[i])
	#print("C12NVoiceConnectors._update_lines(): end")


func _position_line(line_state: LineState) -> void:
	var shorten_len := _c12n.radius * .21
	var start_center_pos := _c12n._get_position_for_pitchclass(line_state.start_pitch)
	var end_center_pos := _c12n._get_position_for_pitchclass(line_state.end_pitch)
	var dir_vec := (end_center_pos - start_center_pos).normalized()
	line_state.line.set_point_position(0, start_center_pos + dir_vec * shorten_len)
	line_state.line.set_point_position(1, end_center_pos - dir_vec * shorten_len)


#endregion


#region animations

## Given structured information about the song, create a list of animations to play at set times.
## Full return type: Dictionary[Node, Dictionary[String(property), Array[Keyframe]]
func hrmn_animate(music_data: Dictionary) -> Dictionary[Node, Dictionary]:
	print_verbose("C12NVoiceConnector.hrmn_animate(): start")
	var animations: Dictionary[Node, Dictionary] = {}

	## animate chord roots
	print_verbose("C12NVoiceConnector.hrmn_animate(): animating chord roots")
	var chord_roots: Array[Dictionary] = Array(Utils.as_array(music_data["chord_roots"]), TYPE_DICTIONARY, "", null)
	animations = Utils.merge_animations(animations, animate_chord_roots(chord_roots))
	
	print_verbose("C12NVoiceConnector.hrmn_animate(): end")
	return animations


func animate_chord_roots(chord_roots: Array[Dictionary]) -> Dictionary[Node, Dictionary]:
	print_verbose("C12NVoiceConnector.animate_chord_roots(): start")
	var anims: Dictionary[Node, Dictionary] = {}

	var selected_pitches: Array[int] = []
	var previous_line_states: Dictionary[Node, Color] = {} # TODO maybe expand Color into a full LineState?

	for chord_root: Dictionary in chord_roots:
		var time: float = chord_root["time"]
		var newest_pitch_class: int = chord_root["elem"]["pitchClass"]
		print_verbose("  start loop. time=%f, newest_pitch_class=%d" % [time, newest_pitch_class])
		
		if selected_pitches.size() == 0:
			# only operate on pairs of selected pitches
			selected_pitches.append(newest_pitch_class)
			continue
		var previous_pitch_class := selected_pitches[-1]
		if newest_pitch_class == previous_pitch_class:
			# same pitch, no need to animate
			continue
		# new chord! we want to animate it
		selected_pitches.append(newest_pitch_class)
		print_verbose("    new selected_pitches=%s, previous_pitch_class=%d" % [selected_pitches, previous_pitch_class])
		
		# setup for adding a line
		var new_line := Line2D.new()
		new_line.default_color = Color.TRANSPARENT
		new_line.width = 1
		new_line.name = "C12NLine%d_%sto%s" % [_lines.size()+1,
			Utils.Pitch.pitchclass_to_pitchname(previous_pitch_class),
			Utils.Pitch.pitchclass_to_pitchname(newest_pitch_class)]
		var line_state := LineState.create(previous_pitch_class, newest_pitch_class, new_line)
		new_line.add_point(Vector2.ZERO)
		new_line.add_point(Vector2.ZERO)
		_position_line(line_state)
		_lines.append(line_state)
		_c12n.add_child(new_line)
		anims[new_line] = {"default_color": [Utils.PropertyKeyframePoint.new(Color.TRANSPARENT, 0)]}
		previous_line_states[new_line] = Color.TRANSPARENT
		# TODO: debug incorrect line colors set in keyframes
		
		# setup for removing a line
		if _voice.max_active != null and selected_pitches.size() > _voice.max_active.v:
			# remove from selected pitches
			selected_pitches.pop_front()
			print_verbose("    removing a line. _voice.max_active.v=%d, selected_pitches.size()=%d, _lines.size()=%d" % [_voice.max_active.v, selected_pitches.size(), _lines.size()])
			# add PropertyChange for turning off this line
			var old_line_idx := _lines.size() - selected_pitches.size()
			var old_line := _lines[old_line_idx].line
			Utils.as_array(anims[old_line]["default_color"]).append(Utils.PropertyKeyframePoint.new(Color.TRANSPARENT, time, 0.0, 0.1, -4.0))
		
		print_verbose("    setting up for new selected_pitches: %s at time %ss" % [selected_pitches, time])
		
		for i in range(selected_pitches.size() - 1):
			var line_idx := _lines.size() - 1 - i
			#var color := Color(1.0, 1.0, 1.0, 0.6) ** i # doesn't work :(
			var new_color := Color.WHITE
			new_color.a = _voice.alpha_decay_factor ** (i+1)
			var selected_line := _lines[line_idx].line
			Utils.as_array(anims[selected_line]["default_color"]).append(Utils.PropertyKeyframePoint.new(new_color, time, 0.0, 0.1, -4.0))
			print_verbose("      i=%d, line_idx=%d, previous_color=%s, new_color=%s" % [i, line_idx, previous_line_states[selected_line], new_color])
			previous_line_states[selected_line] = new_color
	
	print_verbose("C12NVoiceConnector.animate_chord_roots(): end")
	return anims


#endregion
