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

## NodeProvider registration for re-used Line2D nodes
var _line_registration: NodeProvider.NodeTypeRegistration = Utils.NODE_PROVIDER.register(
	self.get_script().get_global_name(),
	"Line2D",
	_create_line,
	func () -> void: pass,
	{"default_color": Color.TRANSPARENT},
)

## unique ids used for re-used Line2Ds
var _next_line_id := 0


# Problem: how to initialize line position properly when activated?
# options:
# 1. set points in animation track. problem: will probably conflict with signals that update it too.
# 2. Call Method track. problem: doesn't run in editor preview.
# 3. animate a dummy property with setter which calls desired function. god i hate this
var _line_state_trigger: int:
	set(value):
		var line_to_update := _lines[value]
		# TODO: perf: stop calling _position_line so often. debounce, memoize, or change animation track?
		print_verbose("calling _position_line from _line_state_trigger setter = %s. line_to_update=%s" % [value, line_to_update])
		_position_line(line_to_update)
		print_verbose("done calling _position_line setter")

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

func _create_line(player: AnimationPlayer, animation: Animation) -> Line2D:
	var new_line := Line2D.new()
	new_line.default_color = Color.TRANSPARENT
	new_line.width = 1
	new_line.name = "C12NLine_%d" % [_next_line_id]
	_next_line_id += 1
	new_line.add_point(Vector2.ZERO)
	new_line.add_point(Vector2.ZERO)
	_c12n.add_child(new_line)

	# Set a transparent keyframe at the very beginning for this line
	var track_idx := Utils.find_or_make_track(player, animation, new_line, "default_color", Animation.TYPE_VALUE)
	animation.track_insert_key(track_idx, 0, Color.TRANSPARENT, 0.0)

	return new_line


func _update_lines() -> void:
	if not is_node_ready():
		return
	#print("C12NVoiceConnectors._update_lines(): start. _lines = %s" % [_lines])
	for i in range(_lines.size()):
		_position_line(_lines[i])
	#print("C12NVoiceConnectors._update_lines(): end")


func _position_line(line_state: LineState) -> void:
	if line_state == null:
		printerr("C12NVoiceConnector._position_line() called with null arg! skipping")
		return
	var arr := _compute_line_pos(line_state)
	var line := line_state.peek_line()
	if line == null:
		printerr("C12NVoiceConnector._position_line() got null Line2D from line_state.peek_line()! skipping")
		return
	line.points = arr


func _compute_line_pos(line_state: LineState) -> PackedVector2Array:
	var shorten_len := _c12n.radius * .21
	var start_center_pos := _c12n._get_position_for_pitchclass(line_state.start_pitch)
	var end_center_pos := _c12n._get_position_for_pitchclass(line_state.end_pitch)
	var dir_vec := (end_center_pos - start_center_pos).normalized()
	var line_start_pos := start_center_pos + dir_vec * shorten_len
	var line_end_pos := end_center_pos - dir_vec * shorten_len
	return PackedVector2Array([line_start_pos, line_end_pos])


#endregion


#region animations

## Given structured information about the song, create a list of animations to play at set times.
## Full return type: Dictionary[Union[Node, NodePromise], Dictionary[String(property), Array[Keyframe]]
func hrmn_animate(music_data: Dictionary) -> Dictionary[Variant, Dictionary]:
	print_verbose("C12NVoiceConnector.hrmn_animate(): start")
	var animations: Dictionary[Variant, Dictionary] = {}

	## animate chord roots
	print_verbose("C12NVoiceConnector.hrmn_animate(): animating chord roots")
	var chord_roots: Array[Dictionary] = Array(Utils.as_array(music_data["chord_roots"]), TYPE_DICTIONARY, "", null)
	animations = Utils.merge_animations(animations, animate_chord_roots(chord_roots))

	print_verbose("C12NVoiceConnector.hrmn_animate(): end")
	return animations


func animate_chord_roots(chord_roots: Array[Dictionary]) -> Dictionary[Variant, Dictionary]:
	print_verbose("C12NVoiceConnector.animate_chord_roots(): start")
	var anims: Dictionary[Variant, Dictionary] = {}

	anims[self] = {"_line_state_trigger": []}

	var selected_pitches: Array[int] = []
	var previous_line_states: Dictionary[NodeProvider.NodePromise, Color] = {} # TODO maybe expand Color into a full LineState?

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
		var new_line := _line_registration.request(time)
		var line_state := LineState.create(previous_pitch_class, newest_pitch_class, new_line)
		_lines.append(line_state)
		anims[new_line] = {"default_color": []}
		#var line_pos := _compute_line_pos(line_state) # can't directly position line imperatively here, must be done via animated property
		# this will cause the line position to be updated
		Utils.as_array(anims[self]["_line_state_trigger"]).append(Utils.PropertyKeyframePoint.new(_lines.size() - 1, time, 0.0))
		previous_line_states[new_line] = Color.TRANSPARENT

		# setup for removing a line
		if _voice.max_active != null and selected_pitches.size() > _voice.max_active.v:
			# remove from selected pitches
			selected_pitches.pop_front()
			print_verbose("    removing a line. _voice.max_active.v=%d, selected_pitches.size()=%d, _lines.size()=%d" % [_voice.max_active.v, selected_pitches.size(), _lines.size()])
			# add PropertyChange for turning off this line
			var old_line_idx := _lines.size() - selected_pitches.size()
			var old_line := _lines[old_line_idx].line_promise
			old_line.done(time) # tell the promise that this is when we're done with this line
			Utils.as_array(anims[old_line]["default_color"]).append(Utils.PropertyKeyframePoint.new(Color.TRANSPARENT, time, 0.0, 0.1, -4.0))
			# add a trigger for positioning line here (in case user is scrubbing backwards on timeline)
			Utils.as_array(anims[self]["_line_state_trigger"]).append(Utils.PropertyKeyframePoint.new(old_line_idx, time + 0.001, 0.0))

		print_verbose("    setting up for new selected_pitches: %s at time %ss" % [selected_pitches, time])

		for i in range(selected_pitches.size() - 1):
			var line_idx := _lines.size() - 1 - i
			#var color := Color(1.0, 1.0, 1.0, 0.6) ** i # doesn't work :(
			var new_color := Color.WHITE
			new_color.a = _voice.alpha_decay_factor ** (i+1)
			var selected_line := _lines[line_idx].line_promise
			print_verbose("      i=%d, line_idx=%d, previous_color=%s, new_color=%s" % [i, line_idx, previous_line_states[selected_line], new_color])
			# print(anims)
			# print(anims[selected_line])
			Utils.as_array(anims[selected_line]["default_color"]).append(Utils.PropertyKeyframePoint.new(new_color, time, 0.0, 0.1, -4.0))
			previous_line_states[selected_line] = new_color

	# set end_times for all remaining nodes
	var end_time: float = chord_roots[-1]["time"] + 10.0
	for i in range(selected_pitches.size()):
		_lines[-i].line_promise.done(end_time)


	print_verbose("C12NVoiceConnector.animate_chord_roots(): end")
	return anims


#endregion
