"""
MusPy
=====

A Python package for processing symbolic music and working with common music
datasets.

"""
from . import (
    classes,
    core,
    datasets,
    inputs,
    metrics,
    music,
    outputs,
    schemas,
    visualization,
)
from .classes import *  # noqa: F401,F403
from .core import *  # noqa: F401,F403
from .datasets import *  # noqa: F401,F403
from .inputs import *  # noqa: F401,F403
from .music import *  # noqa: F401,F403
from .outputs import *  # noqa: F401,F403
from .schemas import *  # noqa: F401,F403
from .version import __version__

__all__ = [
    "__version__",
    "classes",
    "core",
    "datasets",
    "inputs",
    "metrics",
    "music",
    "outputs",
    "schemas",
    "visualization",
]
__all__.extend(classes.__all__)
__all__.extend(core.__all__)
__all__.extend(datasets.__all__)
__all__.extend(inputs.__all__)
__all__.extend(music.__all__)
__all__.extend(outputs.__all__)
__all__.extend(schemas.__all__)
