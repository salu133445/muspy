"""Pianoroll input interface."""
from pypianoroll import Multitrack

from ..music import Music


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
    # TODO: Not implemented yet
    return Music()


def from_pianoroll_representation(data) -> Music:
    """Return a Music object converted from a pianoroll representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in pianoroll representation to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # TODO: Not implemented yet
    return Music()
