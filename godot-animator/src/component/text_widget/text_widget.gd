@tool

class_name TextWidget
extends RichTextLabel

enum TextSource {STATIC, LYRICS, CHORDS, KEY}

const DEFAULT_TRANSITION_TIME := 0.2

@export
var text_source: TextSource = TextSource.STATIC

@export
var transition_time: float = DEFAULT_TRANSITION_TIME

## Given data about a piece of music, determine all of the animation steps to apply
## Full return type: Dictionary[Node, Dictionary[String(property), Array[Keyframe]]
func hrmn_animate(music_data: Dictionary) -> Dictionary[Node, Dictionary]:
	match text_source:
		TextSource.LYRICS:
			var lyrics: Array[Dictionary] = Array(Utils.as_array(music_data["lyrics"]), TYPE_DICTIONARY, "", null)
			print(lyrics)
			return animate_lyrics(lyrics)
		TextSource.CHORDS:
			var chords: Array[Dictionary] = Array(Utils.as_array(music_data["chords"]), TYPE_DICTIONARY, "", null)
			return animate_chords(chords)
		TextSource.KEY:
			var keys: Array[Dictionary] = Array(Utils.as_array(music_data["keys"]), TYPE_DICTIONARY, "", null)
			return animate_keys(keys)
		TextSource.STATIC:
			return {} # nothing to animate
		_:
			printerr("TextWidget.hrmn_animate(): ignoring un-implemented Text Source type: %s" % [text_source])
			return {}


func animate_lyrics(lyrics: Array[Dictionary]) -> Dictionary[Node, Dictionary]:
	
	# example dict element
	#{
	  #"elem": [
		#{
		  #"elem": "I",
		  #"offset": 34.0,
		  #"time": 13.333333333333334,
		  #"_type": "MusicDataTiming[str]"
		#},
		#{
		  #"elem": "chi",
		  #"offset": 34.5,
		  #"time": 13.5,
		  #"_type": "MusicDataTiming[str]"
		#}
	  #],
	  #"offset": 34.0,
	  #"time": 13.333333333333334,
	  #"_type": "MusicDataTiming[list]"
	#},
	
	var animations: Array[Utils.PropertyKeyframePoint] = [Utils.PropertyKeyframePoint.new("", 0)]
	var animation_map: Dictionary[Node, Dictionary] = {self: {
		"text": animations
	}}
	
	for lyric in lyrics:
		print("starting lyric loop. lyric=%s" % [lyric])
		var syllables: Array[Dictionary] = Array(Utils.as_array(lyric["elem"]), TYPE_DICTIONARY, "", null)
		var syllable_texts: Array[String] = Array(
			syllables.map(func (syllable_dict: Dictionary) -> String: return syllable_dict["elem"]),
			TYPE_STRING, "", null)
		
		# loop over each syllable, adding an animation for each syllable
		for voiced_syllable_idx in range(syllables.size()):
			# animate to this syllable being highlighted, all other syllables grayed out
			var time: float = syllables[voiced_syllable_idx]["time"]
			var new_text_parts: Array[String] = []

			# loop to construct the new_text for this currently-voiced syllable
			for processing_syllable_idx in range(syllables.size()):
				# add dash between syllables
				if processing_syllable_idx > 0:
					new_text_parts.append("[color=dark_gray]-[/color]")
				# add currently-processed syllable; pick color based on whether it's voiced or not
				var this_syllable := syllable_texts[processing_syllable_idx]
				if processing_syllable_idx == voiced_syllable_idx:
					new_text_parts.append(this_syllable)
				else:
					new_text_parts.append("[color=dark_gray]%s[/color]" % [this_syllable])
			var new_text: String = new_text_parts.reduce(func (acc: String, el: String) -> String: return acc + el, "")
			
			# add animation for this syllable
			
			# if previous animation was too recent, just add this as a single keyframe
			animations.append(Utils.PropertyKeyframePoint.new(new_text, time, 0.0, transition_time, -4.0))
	
	return animation_map


func animate_chords(chords: Array[Dictionary]) -> Dictionary[Node, Dictionary]:
	var animations: Array[Utils.PropertyKeyframePoint] = [Utils.PropertyKeyframePoint.new("", 0)]
	var animation_map: Dictionary[Node, Dictionary] = {self: {
		"text": animations
	}}
	
	for chord in chords:
		var time: float = chord["time"]
		var chord_text: String = chord["elem"]["name"]
		animations.append(Utils.PropertyKeyframePoint.new(chord_text, time, 0.0, transition_time, -4.0))
	
	return animation_map



func animate_keys(keys: Array[Dictionary]) -> Dictionary[Node, Dictionary]:
	var animations: Array[Utils.PropertyKeyframePoint] = [Utils.PropertyKeyframePoint.new("", 0)]
	var animation_map: Dictionary[Node, Dictionary] = {self: {
		"text": animations
	}}
	
	for key in keys:
		var time: float = key["time"]
		var key_text: String = key["elem"]["name"]
		animations.append(Utils.PropertyKeyframePoint.new(key_text, time, 0.0, transition_time, -4.0))
	
	return animation_map
