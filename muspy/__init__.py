"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.
"""
from . import (
    datasets,
    inputs,
    metrics,
    outputs,
    representations,
    schemas,
    visualization,
)
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
from .inputs import *  # noqa: F401,F403
from .music import Music
from .outputs import *  # noqa: F401,F403
from .representations import *  # noqa: F401,F403
from .schemas import *  # noqa: F401,F403
from .utils import (
    append,
    clip,
    quantize,
    quantize_absolute_timing,
    quantize_by_beats,
    sort,
    to_ordered_dict,
    transpose,
)
from .version import __version__

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
    "__version__",
    "append",
    "clip",
    "datasets",
    "metrics",
    "quantize",
    "quantize_absolute_timing",
    "quantize_by_beats",
    "representations",
    "sort",
    "to_ordered_dict",
    "transpose",
    "visualization",
]
__all__.extend(inputs.__all__)
__all__.extend(outputs.__all__)
__all__.extend(representations.__all__)
__all__.extend(schemas.__all__)
