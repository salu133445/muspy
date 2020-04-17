"""Pianoroll output interface."""
from typing import TYPE_CHECKING

from pypianoroll import Multitrack, Track

if TYPE_CHECKING:
    from ..music import Music


def to_pypianoroll(music: "Music") -> Multitrack:
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
    if music.timing.is_symbolic:
        raise NotImplementedError

    multitrack = Multitrack()

    tracks = []
    for track in music.tracks:
        pianoroll = None
        tracks.append(
            Track(pianoroll, track.program, track.is_drum, track.name)
        )
    return multitrack
