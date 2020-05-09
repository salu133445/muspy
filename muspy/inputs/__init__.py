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
from .event import from_event_representation
from .json import load_json
from .midi import from_pretty_midi, read_midi
from .musicxml import read_musicxml
from .note import from_note_representation
from .pianoroll import from_pypianoroll, from_pianoroll_representation
from .token import from_monotoken_representation, from_polytoken_representation
from .wrappers import from_object, from_representation, load, read
from .yaml import load_yaml
from .abc import read_abc_music21

__all__ = [
    "from_event_representation",
    "from_monotoken_representation",
    "from_note_representation",
    "from_object",
    "from_polytoken_representation",
    "from_pretty_midi",
    "from_pypianoroll",
    "from_pianoroll_representation",
    "from_representation",
    "load",
    "load_json",
    "load_yaml",
    "read",
    "read_midi",
    "read_musicxml",
    "read_abc_music21"
]
