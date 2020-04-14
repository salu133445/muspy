"""Input interface."""
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
