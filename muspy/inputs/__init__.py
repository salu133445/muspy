"""Input interfaces.

MusPy provides the following input interfaces.

- Load from saved objects: :func:`muspy.load_json` and :func:`muspy.load_yaml`
- Read from other formats: :func:`muspy.read_midi` and
  :func:`muspy.read_musicxml`
- Convert from other objects: :func:`muspy.from_pretty_midi` and
  :func:`muspy.from_pypianoroll`
- Wrappers: :func:`muspy.load`, :func:`muspy.read` and :func:`muspy.from_object`

"""
from .json import load_json
from .midi import from_pretty_midi, read_midi
from .musicxml import read_musicxml
from .pianoroll import from_pypianoroll
from .wrappers import from_object, load, read
from .yaml import load_yaml

__all__ = [
    "from_object",
    "from_pretty_midi",
    "from_pypianoroll",
    "load",
    "load_json",
    "load_yaml",
    "read",
    "read_midi",
    "read_musicxml",
]
