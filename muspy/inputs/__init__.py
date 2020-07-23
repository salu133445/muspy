"""
Input Interfaces
================

MusPy provides the following input interfaces.

- Load from saved objects: :func:`muspy.load_json` and :func:`muspy.load_yaml`
- Read from other formats: :func:`muspy.read_midi` and
  :func:`muspy.read_musicxml`
- Convert from other objects: :func:`muspy.from_pretty_midi` and
  :func:`muspy.from_pypianoroll`
- Wrappers: :func:`muspy.load`, :func:`muspy.read` and
  :func:`muspy.from_object`

"""
from .abc import read_abc, read_abc_string
from .event import from_event_representation
from .json import load_json
from .midi import from_pretty_midi, read_midi, MIDIError
from .music21 import from_music21, from_music21_opus
from .musicxml import read_musicxml, MusicXMLError
from .note import from_note_representation
from .pianoroll import from_pianoroll_representation, from_pypianoroll
from .token import from_monotoken_representation, from_polytoken_representation
from .wrappers import from_object, from_representation, load, read
from .yaml import load_yaml

__all__ = [
    "MIDIError",
    "MusicXMLError",
    "from_event_representation",
    "from_monotoken_representation",
    "from_music21",
    "from_music21_opus",
    "from_note_representation",
    "from_object",
    "from_pianoroll_representation",
    "from_polytoken_representation",
    "from_pretty_midi",
    "from_pypianoroll",
    "from_representation",
    "load",
    "load_json",
    "load_yaml",
    "read",
    "read_abc",
    "read_abc_string",
    "read_midi",
    "read_musicxml",
]
