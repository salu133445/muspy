"""Token-based representation output interface."""
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from ..processor import MonoTokenProcessor

if TYPE_CHECKING:
    from ..music import Music


def to_monotoken_representation(music: "Music", min_step: int = 1) -> ndarray:
    """Return a Music object in monotoken-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted monotoken-based representation.
        size: L * D:
            - L for the sequence length
            - D = 1 {
                0-127: pitch onset
                128: hold state
                129: rest state
            }
        e.g.

        [C5 - - - E5 - - / G5 - - / /]
        ->
        [60, 128, 128, 128, 64, 128, 128, 129, 67, 128, 128, 129, 129]

    """
    if len(music.tracks) > 1:
        raise ValueError(
            "Mono token representation only works for single-track music."
        )
    notes = music.tracks[0].notes
    notes.sort(key=lambda x: x.time)
    processor = MonoTokenProcessor(min_step=min_step)
    return np.array(processor.encode(notes))


def to_polytoken_representation(music: "Music", **kwargs) -> ndarray:
    """Return a Music object in polytoken-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted polytoken-based representation.

    """
    raise NotImplementedError
