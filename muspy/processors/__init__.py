"""Representation processors.

This module defines the processors for commonly used representations.

Classes
-------

- NoteRepresentationProcessor
- EventRepresentationProcessor
- AdvancedEventRepresentationProcessor
- PianoRollRepresentationProcessor
- PitchRepresentationProcessor

"""

from .processors import (NoteRepresentationProcessor,
                         PianoRollRepresentationProcessor,
                         PitchRepresentationProcessor,
                         EventRepresentationProcessor)
from .advanced_event import AdvancedEventRepresentationProcessor


__all__ = [
    'NoteRepresentationProcessor',
    'EventRepresentationProcessor',
    'AdvancedEventRepresentationProcessor',
    'PianoRollRepresentationProcessor',
    'PitchRepresentationProcessor',
]
