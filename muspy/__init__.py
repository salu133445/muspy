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
from .schemas import DEFAULT_SCHEMA_VERSION
from .utils import (
    append,
    clip,
    quantize,
    quantize_absolute_timing,
    quantize_by_beats,
    transpose,
)
from .version import __version__

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
    "__version__",
    "append",
    "clip",
    "datasets",
    "load",
    "load_json",
    "load_yaml",
    "metrics",
    "quantize",
    "quantize_absolute_timing",
    "quantize_by_beats",
    "read",
    "read_midi",
    "read_musicxml",
    "representations",
    "save",
    "save_json",
    "save_yaml",
    "transpose",
    "visualization",
    "write",
    "write_midi",
    "write_musicxml",
]
