"""
Output Interfaces
=================

MusPy provides the following output interfaces.

- Save losslessly to JSON or YAML: :func:`muspy.save_json` and
  :func:`muspy.save_yaml`
- Write to other formats: :func:`muspy.write_midi` and
  :func:`muspy.write_musicxml`
- Convert to other objects: :func:`muspy.to_pretty_midi` and
  :func:`muspy.to_pypianoroll`
- Wrappers: :func:`muspy.save`, :func:`muspy.write` and :func:`muspy.to_object`

"""
from .event import to_event_representation
from .json import save_json
from .midi import to_pretty_midi, write_midi
from .musicxml import write_musicxml
from .note import to_note_representation
from .pianoroll import to_pianoroll_representation, to_pypianoroll
from .token import to_monotoken_representation, to_polytoken_representation
from .wrappers import save, to_object, to_representation, write
from .yaml import save_yaml

__all__ = [
    "save",
    "save_json",
    "save_yaml",
    "to_event_representation",
    "to_monotoken_representation",
    "to_note_representation",
    "to_object",
    "to_pianoroll_representation",
    "to_polytoken_representation",
    "to_pretty_midi",
    "to_pypianoroll",
    "to_representation",
    "write",
    "write_midi",
    "write_musicxml",
]
