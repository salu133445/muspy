"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.
"""

from muspy.classes import (
    Annotation,
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SongInfo,
    SourceInfo,
    Tempo,
    TimeSignature,
    TimingInfo,
    Track,
)
from muspy.music import Music

__all__ = [
    "Annotation",
    "KeySignature",
    "MetaData",
    "SongInfo",
    "SourceInfo",
    "Lyric",
    "Note",
    "Music",
    "TimeSignature",
    "Track",
    "Tempo",
    "TimingInfo",
]
