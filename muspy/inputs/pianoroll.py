"""Piano-roll input interface."""
from operator import attrgetter

import numpy as np
from numpy import ndarray

from pypianoroll import Multitrack

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_pypianoroll(m: Multitrack) -> Music:
    """Return a Music object converted from a Pypianoroll Multitrack object.

    Parameters
    ----------
    obj : :class:`pypianoroll.Multitrack` object
        Multitrack object to convert.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    raise NotImplementedError


def from_pianoroll_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    encode_velocity: bool = True,
    default_velocity: int = 64,
) -> Music:
    """Decode pitch-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in piano-roll representation to decode. Will be casted to
        integer if not of integer type. If `encode_velocity` is True,
        will be casted to boolean if not of boolean type.
    resolution : int
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    program : int, optional
        Program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand
        Piano).
    is_drum : bool, optional
        A boolean indicating if it is a percussion track. Defaults to
        False.
    encode_velocity : bool
        Whether to encode velocities. Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    Returns
    -------
    :class:`muspy.Music` object
        Decoded Music object.

    """
    if encode_velocity and not np.issubdtype(array.dtype, np.integer):
        array = array.astype(np.int)
    elif not encode_velocity and not np.issubdtype(array.dtype, np.bool):
        array = array.astype(np.bool)

    binarized = array > 0
    diff = np.diff(binarized, axis=0, prepend=0, append=0)
    notes = []
    for i in range(128):
        boundaries = np.nonzero(diff[:, i])[0]
        for note_idx in range(len(boundaries) // 2):
            start = boundaries[2 * note_idx]
            end = boundaries[2 * note_idx + 1]
            if encode_velocity:
                velocity = array[start, i]
            else:
                velocity = default_velocity
            note = Note(
                time=start, duration=end - start, pitch=i, velocity=velocity,
            )
            notes.append(note)

    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
