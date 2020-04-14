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
from .io import from_dict, load, read, save, write
from .music import Music
from .representations import to_representation
from .schemas import DEFAULT_SCHEMA_VERSION
from .utils import (
    append,
    clip,
    quantize,
    quantize_absolute_timing,
    quantize_by_beats,
    transpose,
    to_ordered_dict,
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
    "from_dict",
    "load",
    "metrics",
    "quantize",
    "quantize_absolute_timing",
    "quantize_by_beats",
    "read",
    "representations",
    "save",
    "to_ordered_dict",
    "to_representation",
    "transpose",
    "visualization",
    "write",
]
