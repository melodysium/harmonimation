@tool

extends Control

@onready var harmonimate_button := $HarmonimateButton
@onready var harmonimation_player_label := $WidgetParentSelector/Label

signal harmonimate

func _ready() -> void:
	harmonimate_button.connect("button_up", _harmonimate)
	harmonimation_player_label.text = HarmonimationPlugin.ANIMATION_PLAYER_NODE_NAME
	

func _harmonimate() -> void:
	emit_signal("harmonimate")
