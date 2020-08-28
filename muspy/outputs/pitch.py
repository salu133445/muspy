"""Pitch-based representation output interface."""
from operator import attrgetter
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

if TYPE_CHECKING:
    from ..music import Music


def to_pitch_representation(
    music: "Music", use_hold_state: bool = False
) -> ndarray:
    """Encode a Music object into pitch-based representation.

    The pitch-based represetantion represents music as a sequence of pitch,
    rest and (optional) hold tokens. Only monophonic melodies are compatible
    with this representation. The output shape is T x 1, where T is the
    number of time steps. The values indicate whether the current time step
    is a pitch (0-127), a rest (128) or (optionally) a hold (129).

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to encode.
    use_hold_state : bool
        Whether to use a special state for holds. Defaults to False.

    Returns
    -------
    ndarray, dtype=uint8, shape=(?, 1)
        Encoded array in pitch-based representation.

    """
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes are found
    if not notes:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Initialize the array
    length = max((note.end for note in notes))
    array = np.zeros((length, 1), np.uint8)

    # Fill the array with rests
    if use_hold_state:
        array.fill(128)

    # Encode note pitches
    for note in notes:
        if use_hold_state:
            array[note.time] = note.pitch
            array[note.time + 1 : note.time + note.duration] = 129
        else:
            array[note.time : note.time + note.duration] = note.pitch

    return array
