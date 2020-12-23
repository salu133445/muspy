"""Representation processors.

This module defines the processors for commonly used representations.

Classes
-------

- NoteRepresentationProcessor
- EventRepresentationProcessor
- PianoRollRepresentationProcessor
- PitchRepresentationProcessor

"""

from .processors import *
from .event import EventRepresentationProcessor

__all__ = [
    'NoteRepresentationProcessor',
    'EventRepresentationProcessor',
    'PianoRollRepresentationProcessor',
    'PitchRepresentationProcessor',
]
