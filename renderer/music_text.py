from music.music_constants import Note
from manim import Text

class TextNote(Text):
  def __init__(self, note: Note, **kwargs):
    Text.__init__(self, note.display, **kwargs)
    self.note = note