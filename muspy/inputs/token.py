"""Token-based representation input interface."""
from typing import Any

from ..classes import Track
from ..music import Music
from ..processor import MonoTokenProcessor


def from_monotoken_representation(data, **kwargs: Any) -> Music:
    """Return a Music object converted from a monotoken-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in monotoken-based representation to be converted.
        size: L * D:
            - L for the sequence length
            - D = 1 {
                0-127: pitch onset
                128: hold state
                129: rest state
            }
        e.g.
        [60, 128, 128, 128, 64, 128, 128, 129, 67, 128, 128, 129, 129]
        ->
        [C5 - - - E5 - - / G5 - - / /]
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object. (Only Track - Note has the information)

    """
    repr_seq = list(data)
    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    processor = MonoTokenProcessor(min_step=min_step)
    note_seq = processor.decode(repr_seq)
    return Music(tracks=[Track(notes=note_seq)])


def from_polytoken_representation(data, **kwargs) -> Music:
    """Return a Music object converted from a polytoken-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in polytoken-based representation to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # TODO: Not implemented yet
    return Music()
