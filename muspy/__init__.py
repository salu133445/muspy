"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.
"""
from . import (
    core,
    datasets,
    inputs,
    metrics,
    outputs,
    representations,
    schemas,
    visualization,
)
from .core import *  # noqa: F401,F403
from .inputs import *  # noqa: F401,F403
from .music import Music
from .outputs import *  # noqa: F401,F403
from .representations import *  # noqa: F401,F403
from .schemas import *  # noqa: F401,F403
from .version import __version__

__all__ = [
    "__version__",
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
__all__.extend(core.__all__)
__all__.extend(inputs.__all__)
__all__.extend(outputs.__all__)
__all__.extend(representations.__all__)
__all__.extend(schemas.__all__)
