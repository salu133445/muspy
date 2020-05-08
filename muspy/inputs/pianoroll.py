"""Pianoroll input interface."""
from typing import Any

from pypianoroll import Multitrack

from ..classes import Track
from ..music import Music
from ..processor import PianoRollProcessor


def from_pypianoroll(m: Multitrack) -> Music:
    """Return a Music object converted from a Multitrack object.

    Parameters
    ----------
    obj : :class:`pypianoroll.Multitrack` object
        Multitrack object to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    raise NotImplementedError


def from_pianoroll_representation(
    data, min_step: int = 1, binarized: bool = False, **kwargs: Any
) -> Music:
    """Return a Music object converted from a pianoroll representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in pianoroll representation to be converted.
        size: L * D:
            - L for the sequence (note) length
            - D = 128
                the value in each dimension indicates the velocity
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object. (Only Track - Note has the information)

    """
    processor = PianoRollProcessor(min_step=min_step, binarized=binarized)
    notes = processor.decode(data)
    return Music(tracks=[Track(notes=notes)], **kwargs)
