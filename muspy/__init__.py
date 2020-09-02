"""A toolkit for symbolic music generation.

MusPy is an open source Python library for symbolic music generation. It
provides essential tools for developing a music generation system,
including dataset management, data I/O, data preprocessing and model
evaluation.

Features
--------

- Dataset management system for commonly used datasets with interfaces
  to PyTorch and TensorFlow.
- Data I/O for common symbolic music formats (e.g., MIDI, MusicXML and
  ABC) and interfaces to other symbolic music libraries (e.g., music21,
  mido, pretty_midi and Pypianoroll).
- Implementations of common music representations for music generation,
  including the pitch-based, the event-based, the piano-roll and the
  note-based representations.
- Model evaluation tools for music generation systems, including audio
  rendering, score and piano-roll visualizations and objective metrics.

"""
from . import (
    base,
    classes,
    core,
    datasets,
    external,
    inputs,
    metrics,
    music,
    outputs,
    processors,
    schemas,
    visualization,
)
from .base import *  # noqa: F401,F403
from .classes import *  # noqa: F401,F403
from .core import *  # noqa: F401,F403
from .datasets import *  # noqa: F401,F403
from .external import *  # noqa: F401,F403
from .inputs import *  # noqa: F401,F403
from .metrics import *  # noqa: F401,F403
from .music import *  # noqa: F401,F403
from .outputs import *  # noqa: F401,F403
from .processors import *  # noqa: F401,F403
from .schemas import *  # noqa: F401,F403
from .version import __version__
from .visualization import *  # noqa: F401,F403

__all__ = [
    "__version__",
    "datasets",
    "external",
    "inputs",
    "metrics",
    "outputs",
    "processors",
    "schemas",
    "visualization",
]
__all__.extend(base.__all__)
__all__.extend(classes.__all__)
__all__.extend(core.__all__)
__all__.extend(datasets.__all__)
__all__.extend(external.__all__)
__all__.extend(inputs.__all__)
__all__.extend(metrics.__all__)
__all__.extend(music.__all__)
__all__.extend(outputs.__all__)
__all__.extend(processors.__all__)
__all__.extend(schemas.__all__)
__all__.extend(visualization.__all__)
