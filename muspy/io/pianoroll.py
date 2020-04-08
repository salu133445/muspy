"""Pianoroll I/O utilities."""
from pypianoroll import Multitrack

from ..music import Music


def from_pypianoroll(obj: Multitrack) -> Music:
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
    music = Music()
    # TODO: Not implemented yet
    return music


def to_pypianoroll(music: Music) -> Multitrack:
    """Return a Multitrack object converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    multitrack : :class:`pypianoroll.Multitrack` object
        Converted Multitrack object.
    """
    multitrack = Multitrack()
    # TODO: Not implemented yet
    return multitrack
