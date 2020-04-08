"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.
"""
from . import datasets, metrics, representations, visualization
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
from .io import (
    DEFAULT_SCHEMA_VERSION,
    load,
    load_json,
    load_yaml,
    read,
    read_midi,
    read_musicxml,
    save,
    save_json,
    save_yaml,
    write,
    write_midi,
    write_musicxml,
)
from .music import Music
from .utils import append

__all__ = [
    "Annotation",
    "DEFAULT_SCHEMA_VERSION",
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
    "append",
    "datasets",
    "load",
    "load_json",
    "load_yaml",
    "metrics",
    "read",
    "read_midi",
    "read_musicxml",
    "representations",
    "save",
    "save_json",
    "save_yaml",
    "visualization",
    "write",
    "write_midi",
    "write_musicxml",
]
