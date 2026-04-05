@tool

class_name NodeProvider # TODO: rename to smth like NodeLifetimeManager
extends Node


# TODO: for signals.
# Can't ad-hoc disconnect and re-connect signals at different times in animations. Instead:
# 1. Define a function like get_active_handlers(signal_name, current_time) -> Array[Callable]. Store all data necessary to answer.
# 2. Connect each concrete node for all signals it needs to hear, answered by some signal_multiplex() function that uses get_active_handlers()


#region Types

# TODO: consier making this the top-level class of this script
## Provided to client classes after they register a NodeType.
## Allows them to get NodePromise objects.
class NodeTypeRegistration:
    var _provider: NodeProvider

    ## id of next generated promise
    var _next_id := 0

    ## currently active promises to fulfill
    ## full type: Dictionary[id: int(promise id), NodePromise]
    var _promises: Dictionary[int, NodePromise] = {}

    ## concrete Nodes created to answer
    ## full type: Dictionary[id: int(promise id),Node]
    var _nodes: Dictionary[int, NodeMetadata] = {}

    var _client: Node

    var client_name: String
    var node_type: String

    ## Called during initialization whenever a node is created.
    ## Must have the signature: func (AnimationPlayer, Animation) -> Node
    var init_fn: Callable
    ## Called during animation playback whenever a Promise's start_time or end_time is reached
    ## Must have the signature: func(NodePromise) -> Node
    ## Use this to set properties which cannot be animated on the timeline, i.e. due to updates from signals.
    var activate_fn: Callable

    # save these from the answer() call for sneaky use later
    var _player: AnimationPlayer
    var _animation: Animation

    ## Initial property values to set at time 0 and before this node is activated.
    var initial_prop_values: Dictionary[String, Variant]

    func _init(
        _provider: NodeProvider,
        _client: Node,
        _client_name: String,
        _node_type: String,
        _init_fn: Callable,
        _activate_fn: Callable = func() -> void: {},
        _initial_prop_values: Dictionary[String, Variant] = {},
    ) -> void:
        self._provider = _provider
        self._client = _client
        self.client_name = _client_name
        self.node_type = _node_type
        self.init_fn = _init_fn
        self.activate_fn = _activate_fn
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
        self._player = player
        self._animation = animation
        if promise.end_time < 0:
            printerr("%s does not have an end_time set! Not providing a node." % [promise])
            return null
        if promise.id in _nodes:
            return _nodes[promise.id].node
        print_verbose("NodeProvider.answer(): resolving promise with id=%d" % [promise.id])

        # look for a node that can be re-used
        var node_info := _find_available_node(promise)
        if node_info == null:
            print("No existing node available to answer promise %s; creating new node." % [promise])
            node_info = _init_node(promise, player, animation)
        else:
            node_info.add_promise(promise)

        # register this node as an answer for this promise
        _nodes[promise.id] = node_info

        # set initial_prop_values at start_time and end_time for promise
        var node := node_info.node
        var initial_prop_values := promise._registration.initial_prop_values
        for prop_name in initial_prop_values.keys():
            var prop_value: Variant = initial_prop_values[prop_name]
            var track_idx := Utils.find_or_make_track(player, animation, node, prop_name, Animation.TYPE_VALUE)
            animation.track_insert_key(track_idx, promise.start_time, prop_value, 0.0)
            animation.track_insert_key(track_idx, promise.end_time, prop_value, 0.0)

        # add NodeMetadata as child of the client, and add a keyframe for the activation trigger
        var track_idx := Utils.find_or_make_track(player, animation, node_info, "_activate_trigger", Animation.TYPE_VALUE)
        animation.track_insert_key(track_idx, promise.start_time, promise.id, 0.0)
        animation.track_insert_key(track_idx, promise.end_time, promise.id, 0.0)

        return node

    ## Look for a node which is available to answer the specified promise
    ## A node is available if it is not used by another promise for the entire span of the specified promise
    func _find_available_node(promise: NodePromise) -> NodeMetadata:
        for node_info: NodeMetadata in self._nodes.values():
            if node_info.earliest_start_time > promise.end_time or node_info.latest_end_time < promise.start_time:
                print("Re-using node %s to answer promise %s" % [node_info, promise])
                return node_info
        return null

    func _init_node(promise: NodePromise, player: AnimationPlayer, animation: Animation) -> NodeMetadata:
        print_verbose("NodeProvider._init_node(): creating node due to promise with id=%d" % [promise.id])

        var node: Node = promise._registration.init_fn.call(player, animation)
        var node_info := NodeMetadata.new(node, promise)
        _client.add_child(node_info)

        # Set initial property values
        for prop_name in promise._registration.initial_prop_values.keys():
            var prop_value: Variant = promise._registration.initial_prop_values[prop_name]
            var track_idx := Utils.find_or_make_track(player, animation, node, prop_name, Animation.TYPE_VALUE)
            animation.track_insert_key(track_idx, 0, prop_value, 0.0)

        return node_info

    ## If this promise has been answered, returns the Node it refers to. Otherwise returns null.
    func peek(promise: NodePromise) -> Node:
        if promise.end_time < 0:
            printerr("%s does not have an end_time set! Not providing a node." % [promise])
            return null
        if promise.id in self._nodes:
            return _nodes[promise.id].node
        return null

    ## Based on current time, return a list of all NodePromise objects which should be showing in the animation right now.
    func list_active_promises() -> Array[NodePromise]:
        var active_promises: Array[NodePromise] = []
        var current_time = _player.current_animation_position
        #print("NodeTypeRegistation.list_active_promises(): begin. current_time=%f" % [current_time])
        for promise: NodePromise in self._promises.values():
            #print("NodeTypeRegistation.list_active_promises(): considering promise . current_time=%f" % [current_time])
            if promise.start_time <= current_time and promise.end_time >= current_time:
                active_promises.append(promise)
        return active_promises




    func _scope() -> String:
        return client_name + "::" + node_type

## A token specifying the timespan a node is needed.
## Can be returned in hrmn_animate just like a concrete Node; the animation renderer will resolve the promise when setting keyframes.
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
        #return NodeProvider._scope(client_name, node_type)

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


## Holds the constructed node, as well as metadata about its promises to assist in answering promises.
class NodeMetadata extends Node:
    var node: Node
    var promises: Dictionary[int, NodePromise]
    var registration: NodeTypeRegistration
    # current approach: track furthest start_time & end_time; only add new promises outside of the spanned range
    # TODO: future optimization: allow placing promises in empty gaps where a node isn't used
    var latest_end_time: float
    var earliest_start_time: float

    ## This property is animated in order to trigger _activate_fn() logic provided by client
    var _activate_trigger: int:
        set(value):
            var target_promise = self.promises[value]
            registration.activate_fn.call(target_promise)
            # TODO: perf: figure out how to trigger this only once, rather than interpolating the value between keyframes

    func _init(
        _node: Node,
        _promise: NodePromise,
    ) -> void:
        self.node = _node
        self.promises = {_promise.id: _promise}
        self.registration = _promise._registration
        self.earliest_start_time = _promise.start_time
        self.latest_end_time = _promise.end_time
        self.name = "NodeMetadata[first=%d]" % [_promise.id]

    func add_promise(_promise: NodePromise) -> void:
        promises[_promise.id] = _promise
        self.earliest_start_time = min(self.earliest_start_time, _promise.start_time)
        self.latest_end_time = max(self.latest_end_time, _promise.end_time)
        #self.name = "NodeMetadata[%s]" % self.promises.keys() # changing node name is probably a bad idea

#endregion



#region Internal State

## Known NodeTypeRegistration objects created by this class
var registrations: Dictionary[String, NodeTypeRegistration] = {}


#endregion



#region Private Helpers



#endregion



#region Public API

## Register a node type for optimized use throughout an animation.
## Once this is created, request NodePromise objects from registration.request()
func register(owner: Node, client_name: String, node_type: String, init_fn: Callable, activate_fn: Callable, initial_prop_values: Dictionary[String, Variant] = {}) -> NodeTypeRegistration:
    var registration := NodeTypeRegistration.new(self, owner, client_name, node_type, init_fn, activate_fn, initial_prop_values)
    registrations[registration._scope()] = registration
    return registration

#endregion
