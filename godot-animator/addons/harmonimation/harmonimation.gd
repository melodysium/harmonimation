@tool
extends EditorPlugin

class_name HarmonimationPlugin

const ANIMATION_PLAYER_NODE_NAME = "HarmonimationPlayer"

# A class member to hold the dock during the plugin life cycle.
var dock: HarmonimationEditor

var harmonimation_player: AnimationPlayer = null
# TODO: tie to the AnimationPlayer


func _enable_plugin() -> void:
	# Add autoloads here.
	pass


func _disable_plugin() -> void:
	# Remove autoloads here.
	pass


func _enter_tree() -> void:
	# Initialization of the plugin goes here.
	# Load the dock scene and instantiate it.
	dock = (preload("res://addons/harmonimation/dock_editor/harmonimation_editor.tscn").instantiate())
	# Add the loaded scene to the docks.
	add_control_to_dock(DOCK_SLOT_RIGHT_BL, dock)
	
	dock.harmonimate_button.connect("button_up", _harmonimate)



func _exit_tree() -> void:
	# Clean-up of the plugin goes here.
	# Remove the dock.
	remove_control_from_docks(dock)
	# Erase the control from the memory.
	dock.free()


func _select_animation_player() -> AnimationPlayer:
	var editor_interface = get_editor_interface()
	var scene_root = editor_interface.get_edited_scene_root()
	# try to load just by name as direct child of scene root
	var found_node = scene_root.find_child(ANIMATION_PLAYER_NODE_NAME, false)
	if found_node != null:
		return found_node
	# if still doesn't exist, creat it and add it
	printerr("TODO implement creating AnimationPlayer in user's Scene Tree")
	return null


func _harmonimate() -> void:
	print("harmonimate, go!")
	if harmonimation_player == null: # TODO: also check that it's still within the current edited scene. or maybe just re-pick it every time
		harmonimation_player = _select_animation_player()
	print(harmonimation_player.get_path())
	
	printerr("TODO implement: open file dialog to retrieve musicxml file path (might require adding an EditorImportPlugin)")
	printerr("TODO implement: save the file path in some resource somewhere and just use it as a default going forward unless user changes it")
	printerr("TODO implement: shell command to invoke python script")
	printerr("TODO implement: file watching on the musicxml file?")
	printerr("TODO implement: save output music_data.json of python script as resource file with checksum of the musicxml")
	printerr("TODO implement: scan the editor tree to find all Harmonimation widgets")
	printerr("TODO implement: pass music_data into all Harmonimation widgets, then place into AnimationPlayer")
	
#var _viewport := EditorInterface.get_editor_viewport_2d()
#
#@export_tool_button("Load Musicxml File") var load_musicxml_action := load_musicxml_file
#var _musicxml_file_dialog: EditorFileDialog  = null
#
#func _run() -> void:
	#print("test")
	#load_musicxml_file()
#
#func load_musicxml_file() -> void:
	#print("TODO")
	#_musicxml_file_dialog = EditorFileDialog.new()
	#_musicxml_file_dialog.access = EditorFileDialog.ACCESS_FILESYSTEM
	#_musicxml_file_dialog.file_mode = EditorFileDialog.FILE_MODE_OPEN_FILE
	#_musicxml_file_dialog.add_filter("*.musicxml", "MusicXML (uncompressed)")
	#
	#_viewport.add_child(_musicxml_file_dialog)
	#_musicxml_file_dialog.connect("file_selected", _on_musicxml_file_selected)
	#_musicxml_file_dialog.set_meta("_created_by", self) # needed so the script is not directly freed after the run function. Would disconnect all signals otherwise
	#_musicxml_file_dialog.popup(Rect2(0,0, 700, 500))
	#print("window should be shown")
#
#func _on_musicxml_file_selected(path: String) -> void:
	#print("file selected: ", path)
	#_musicxml_file_dialog.queue_free()
	#
