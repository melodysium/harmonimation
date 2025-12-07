@tool

class_name HarmonimationEditor

extends Control

@onready var harmonimate_button := $HarmonimateButton
@onready var harmonimation_player_label := $WidgetParentSelector/Label

func _ready() -> void:
	harmonimation_player_label.text = HarmonimationPlugin.ANIMATION_PLAYER_NODE_NAME
