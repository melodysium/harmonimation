@tool

class_name NodeProvider # TODO: rename to smth like NodeLifetimeManager
extends Node


# TODO: for signals.
# Can't ad-hoc disconnect and re-connect signals at different times in animations. Instead:
# 1. Define a function like get_active_handlers(signal_name, current_time) -> Array[Callable]. Store all data necessary to answer.
# 2. Connect each concrete node for all signals it needs to hear, answered by some signal_multiplex() function that uses get_active_handlers()


#region Types


## Provided to client classes after they register a NodeType.
## Allows them to get NodePromise objects.
class NodeTypeRegistration:
	var _provider: NodeProvider

	## id of next generated promise
	var _next_id := 0

	## currently active promises to fulfill
	## full type: Dictionary[id: int, NodePromise]
	var _promises: Dictionary[int, NodePromise] = {}

	## concrete Nodes created to answer
	## full type: Dictionary[node_scope: String(owner_name + "::" + node_type), Dictionary[id: int, Node]]
	var _nodes: Dictionary[int, Node] = {}

	var owner_name: String
	var node_type: String

	## Called whenever any node is created.
	## Must have the signature: func (AnimationPlayer, Animation) -> Node
	var init_fn: Callable
	### Called whenever answer() resolves a NodePromise, applying to a previously created node.
	### TODO: Can take some args from Promise constructor.
	#var activate_fn: Callable
	## Called whenever end_time is reached for a given Promise, removing the Node from service until next answer().
	## Must have the signature: func (Node) -> void
	var reset_fn: Callable

	## Initial property values to set at time 0 and before this node is activated.
	var initial_prop_values: Dictionary[String, Variant]

	func _init(
		_provider: NodeProvider,
		_owner_name: String,
		_node_type: String,
		_init_fn: Callable,
		_reset_fn: Callable,
		_initial_prop_values: Dictionary[String, Variant]
	) -> void:
		self._provider = _provider
		self.owner_name = _owner_name
		self.node_type = _node_type
		self.init_fn = _init_fn
		self.reset_fn = _reset_fn
		self.initial_prop_values = _initial_prop_values


	func request(
			start_time: float,
			end_time: float = -1,
			signals: Dictionary[Signal, StringName] = {},
			## Code to run on this  when answering this promise
			#activate_fn: Callable = func (node: Node) -> void: pass,
	) -> NodePromise:
		var id := _next_id
		_next_id += 1
		var promise = NodePromise.new(self, id, start_time, end_time, signals)
		_promises[id] = promise
		return promise


	func answer(promise: NodePromise, player: AnimationPlayer, animation: Animation) -> Node:
		if promise.end_time < 0:
			printerr("%s does not have an end_time set! Not providing a node." % [promise])
			return null
		if promise.id in _nodes:
			return _nodes[promise.id]
		# dummy implementation: always instantiate and return new node
		print_verbose("NodeProvider.answer(): resolving promise for id=%d" % [promise.id])
		# TODO: set initial_prop_values at start_time and end_time
		var node = promise._registration.init_fn.call(player, animation)
		_nodes[promise.id] = node
		# TODO: add property keyframes for all initial_prop_values
		return node

	func peek(promise: NodePromise) -> Node:
		if promise.end_time < 0:
			printerr("%s does not have an end_time set! Not providing a node." % [promise])
			return null
		return _nodes.get(promise.id)


	func _scope() -> String:
		return owner_name + "::" + node_type


class NodePromise:
	var _registration: NodeTypeRegistration
	var id: int
	var start_time: float
	var end_time: float
	## Map of signals to method names to call on the provided Node
	var signals: Dictionary[Signal, StringName]


	func _init(
			__registration: NodeTypeRegistration,
			_id: int,
			_start_time: float,
			_end_time: float,
			_signals: Dictionary[Signal, StringName]) -> void:
		self._registration = __registration
		self.id = _id
		self.start_time = _start_time
		self.end_time = _end_time
		self.signals = _signals


	func done(end_time: float):
		self.end_time = end_time

	func _to_string() -> String:
		return "NodePromise[registration=%s, id=%d, start_time=%f, end_time=%f]" % [_registration._scope(), id, start_time, end_time]

	#func _scope() -> String:
		#return NodeProvider._scope(owner_name, node_type)

	## Only to be called from hrmn_render
	func answer(player: AnimationPlayer, animation: Animation) -> Node:
		return _registration.answer(self, player, animation)

	## Can be called by hrmn widgets, but will return null if promise is not yet answered.
	func peek() -> Node:
		return _registration.peek(self)

	# TODO: figure out how to handle signals better
	# TODO: maybe replace with a single "listener" per node that just does the filtering? so less connections...
	#func _handle_signal(_signal: Signal) -> void:
		#if self.signals.has(_signal):
			#if _provider.current_time > self.start_time and _provider.current_time < self.end_time:
				#self.answer().call(self.signals[_signal])

# TODO: document
# TODO: use this struct for re-using nodes
class NodeMetadata:
	var node: Node
	var latest_end_time: float

	func _init(
		_node: Node,
		_latest_end_time: float,
	) -> void:
		self.node = _node
		self.latest_end_time = _latest_end_time

#endregion



#region Internal State

## Known NodeTypeRegistration objects created by this class
var registrations: Dictionary[String, NodeTypeRegistration] = {}


#endregion



#region Private Helpers



#endregion



#region Public API

# TODO: animate in hrmn_renderer
## Used to filter out signals called at times when a node is not active
#@export
#var current_time: float = 0.0

## Register a node type for optimized use throughout an animation.
## Once this is created, request NodePromise objects from registration.request()
func register(owner: String, node_type: String, init_fn: Callable, reset_fn: Callable, initial_prop_values: Dictionary[String, Variant] = {}) -> NodeTypeRegistration:
	var registration := NodeTypeRegistration.new(self, owner, node_type, init_fn, reset_fn, initial_prop_values)
	registrations[registration._scope()] = registration
	return registration

#endregion
