@tool

class_name NodeProvider # TODO: rename to smth like NodeLifetimeManager
extends Node


# TODO: for signals.
# Can't ad-hoc disconnect and re-connect signals at different times in animations. Instead:
# 1. Define a function like get_active_handlers(signal_name, current_time) -> Array[Callable]. Store all data necessary to answer.
# 2. Connect each concrete node for all signals it needs to hear, answered by some signal_multiplex() function that uses get_active_handlers()


#region Types


class NodeTypeRegistration:
	var node_type: String
	var init_fn: Callable
	var reset_fn: Callable
	
	func _init(
		_node_type: String,
		_init_fn: Callable,
		_reset_fn: Callable,
	) -> void:
		self.node_type = _node_type
		self.init_fn = _init_fn
		self.reset_fn = _reset_fn

# TODO: figure out how to return this in the hrmn_animate function. Maybe I just make the Dictionary key a Variant, duck-typed as either Node or NodePromise?
class NodePromise:
	var _provider: NodeProvider
	var id: int
	var node_type: String
	var start_time: float
	var end_time: float
	## Map of signals to method names to call on the provided Node
	var signals: Dictionary[Signal, StringName]
	
	func _init(
			__provider: NodeProvider,
			_id: int,
			_node_type: String,
			_start_time: float,
			_signals: Dictionary[Signal, StringName]) -> void:
		self._provider = __provider
		self.id = _id
		self.node_type = _node_type
		self.start_time = _start_time
		self.signals = _signals
	
	## Only to be called from hrmn_render
	func answer() -> Node:
		return _provider._answer_promise(self)
	
	# TODO: register this as a listener
	# TODO: maybe replace with a single "listener" per node that just does the filtering? so less connections...
	func _handle_signal(_signal: Signal) -> void:
		if self.signals.has(_signal):
			if _provider.current_time > self.start_time and _provider.current_time < self.end_time:
				self.answer().call(self.signals[_signal])
		


#endregion



#region Internal State

## Map of registered node types that this Provider class knows how to instantiate and return
var _class_db: Dictionary[String, NodeTypeRegistration]

## promise id to use for next call to request()
var _next_id := 0

# TODO: add parent to the structure here. maybe use a struct[String(node_type), Node(parent)] as the index? or a double-layer Dict?
## currently active promises to fulfill
## full type: Dictionary[int, Dictionary[int, NodePromise]
var _promises: Dictionary[String, Dictionary] = {} 

## concrete Nodes created to answer 
## full type: Dictionary[String, Dictionary[int, Node]]
var _nodes: Dictionary[String, Dictionary] = {} 

#endregion



#region Private Helpers

func _answer_promise(promise: NodePromise) -> Node:
	return null # TODO: implement


#endregion



#region Public API

# TODO: animate in hrmn_renderer
## Used to filter out signals called at times when a node is not active
@export
var current_time: float = 0.0

# TODO: consider adding: parent (for add to tree)
func register(node_type: String, init_fn: Callable, reset_fn: Callable) -> void:
	if _class_db.has(node_type):
		printerr("Node type %s already registered! Please only register each node type once." % [node_type])
		return
	_class_db[node_type] = NodeTypeRegistration.new(node_type, init_fn, reset_fn)


func request(node_type: String, start_time: float, signals: Dictionary[Signal, StringName] = {}) -> NodePromise:
	if !_class_db.has(node_type):
		printerr("Cannot request node of type %s if it has not been registered first. Please call register() for this node type before calling request()." % [node_type])
		return null
	var id := _next_id
	_next_id += 1
	return NodePromise.new(self, id, node_type, start_time, signals)


func done(promise: NodePromise, end_time: float):
	promise.end_time = end_time

#endregion
