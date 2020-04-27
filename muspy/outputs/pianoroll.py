"""Pianoroll output interface."""
from typing import TYPE_CHECKING

from numpy import ndarray
from pypianoroll import Multitrack, Track

if TYPE_CHECKING:
    from ..music import Music


def to_pypianoroll(music: "Music") -> Multitrack:
    """Return a Music object as a Multitrack object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    multitrack : :class:`pypianoroll.Multitrack` object
        Converted Multitrack object.

    """
    if music.timing.is_symbolic:
        raise NotImplementedError

    multitrack = Multitrack()

    tracks = []
    for track in music.tracks:
        # TODO: Not implemented yet
        pianoroll = None
        tracks.append(
            Track(pianoroll, track.program, track.is_drum, track.name)
        )
    return multitrack


def to_pianoroll_representation(music: "Music") -> ndarray:
    """Return a Music object in pianoroll representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted pianoroll representation.

    """
    # TODO: Not implemented yet
    return ndarray()
