"""Representation processors.

This module defines the processors for commonly used representations.

Classes
-------

- NoteRepresentationProcessor
- EventRepresentationProcessor
- PianoRollRepresentationProcessor
- PitchRepresentationProcessor

"""

from .processors import (NoteRepresentationProcessor,
                         PianoRollRepresentationProcessor,
                         PitchRepresentationProcessor,
                         EventRepresentationProcessor)


__all__ = [
    'NoteRepresentationProcessor',
    'EventRepresentationProcessor',
    'PianoRollRepresentationProcessor',
    'PitchRepresentationProcessor',
]
