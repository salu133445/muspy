"""Output interface.

MusPy provides the following output interfaces.

- Save losslessly to JSON or YAML: :func:`muspy.save_json` and
  :func:`muspy.save_yaml`
- Write to other formats: :func:`muspy.write_midi` and
  :func:`muspy.write_musicxml`
- Convert to other objects: :func:`muspy.to_pretty_midi` and
  :func:`muspy.to_pypianoroll`
- Wrappers: :func:`muspy.save`, :func:`muspy.write` and :func:`muspy.to_object`

"""
from .midi import to_pretty_midi, write_midi
from .wrappers import save, to_object, write
from .pianoroll import to_pypianoroll
from .yaml import save_yaml
from .json import save_json
from .musicxml import write_musicxml

__all__ = [
    "save",
    "save_json",
    "save_yaml",
    "to_object",
    "to_pretty_midi",
    "to_pypianoroll",
    "write",
    "write_midi",
    "write_musicxml",
]
