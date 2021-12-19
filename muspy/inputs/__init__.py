"""Input interfaces.

This module provides input interfaces for common symbolic music formats,
MusPy's native JSON and YAML formats, other symbolic music libraries and
commonly-used representations in music generation.

Functions
---------

- from_event_representation
- from_mido
- from_music21
- from_music21_opus
- from_note_representation
- from_object
- from_pianoroll_representation
- from_pitch_representation
- from_pretty_midi
- from_pypianoroll
- from_representation
- load
- load_json
- load_yaml
- read
- read_abc
- read_abc_string
- read_midi
- read_musescore
- read_musicxml

Errors
------

- MIDIError
- MusicXMLError

"""
from .abc import read_abc, read_abc_string
from .event import from_event_representation
from .json import load_json
from .midi import MIDIError, from_mido, from_pretty_midi, read_midi
from .musescore import MuseScoreError, read_musescore
from .music21 import (
    from_music21,
    from_music21_opus,
    from_music21_part,
    from_music21_score,
)
from .musicxml import MusicXMLError, read_musicxml
from .note import from_note_representation
from .pianoroll import (
    from_pianoroll_representation,
    from_pypianoroll,
    from_pypianoroll_track,
)
from .pitch import from_pitch_representation
from .wrappers import from_object, from_representation, load, read
from .yaml import load_yaml

__all__ = [
    "MIDIError",
    "MuseScoreError",
    "MusicXMLError",
    "from_event_representation",
    "from_mido",
    "from_music21",
    "from_music21_opus",
    "from_music21_part",
    "from_music21_score",
    "from_note_representation",
    "from_object",
    "from_pianoroll_representation",
    "from_pitch_representation",
    "from_pretty_midi",
    "from_pypianoroll",
    "from_pypianoroll_track",
    "from_representation",
    "load",
    "load_json",
    "load_yaml",
    "read",
    "read_abc",
    "read_abc_string",
    "read_midi",
    "read_musescore",
    "read_musicxml",
]
