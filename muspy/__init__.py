"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.
"""
from . import datasets, io, metrics, representations, schemas, visualization
from .classes import (
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
from .music import Music

__all__ = [
    "Annotation",
    "KeySignature",
    "Lyric",
    "MetaData",
    "Music",
    "Note",
    "SongInfo",
    "SourceInfo",
    "Tempo",
    "TimeSignature",
    "TimingInfo",
    "Track",
    "datasets",
    "io",
    "representations",
    "metrics",
    "visualization",
    "schemas",
]
