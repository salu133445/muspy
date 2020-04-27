"""Pianoroll output interface."""
from typing import TYPE_CHECKING

import numpy as np
from pypianoroll import Multitrack, Track
from ..processor import PianoRollProcessor

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


def to_pianoroll_representation(music: "Music", **kwargs) -> np.ndarray:
    """Return a Music object in pianoroll representation.

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
        Converted pianoroll representation.
        size: L * D:
            - L for the sequence (note) length
            - D = 128
                the value in each dimension indicates the velocity

    """
    if not music.timing.is_symbolic:
        raise Exception("object is not symbolic", music.timing)
    note_seq = []
    for track in music.tracks:
        note_seq.extend(track.notes)

    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    note_seq.sort(key=lambda x: x.start)
    processor = PianoRollProcessor(min_step=min_step)
    repr_seq = processor.encode(note_seq)
    return np.array(repr_seq)
