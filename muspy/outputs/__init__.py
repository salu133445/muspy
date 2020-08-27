"""
Output Interfaces
=================

This module provides output interfaces for common symbolic music
formats, MusPy's native JSON and YAML formats, other symbolic music
libraries and commonly-used representations in music generation.

"""
from .event import to_event_representation
from .json import save_json
from .midi import to_pretty_midi, write_midi
from .music21 import to_music21
from .musicxml import write_musicxml
from .note import to_note_representation
from .pianoroll import to_pianoroll_representation, to_pypianoroll
from .pitch import to_pitch_representation
from .wrappers import save, to_object, to_representation, write
from .yaml import save_yaml

__all__ = [
    "save",
    "save_json",
    "save_yaml",
    "to_event_representation",
    "to_music21",
    "to_note_representation",
    "to_object",
    "to_pianoroll_representation",
    "to_pitch_representation",
    "to_pretty_midi",
    "to_pypianoroll",
    "to_representation",
    "write",
    "write_midi",
    "write_musicxml",
]
