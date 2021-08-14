"""Note-based representation output interface."""
from operator import attrgetter
from typing import TYPE_CHECKING, Union

import numpy as np
from numpy import ndarray

from ..classes import DEFAULT_VELOCITY

if TYPE_CHECKING:
    from ..music import Music


def to_note_representation(
    music: "Music",
    use_start_end: bool = False,
    encode_velocity: bool = True,
    dtype: Union[np.dtype, type, str] = int,
) -> ndarray:
    """Encode a Music object into note-based representation.

    The note-based represetantion represents music as a sequence of
    (time, pitch, duration, velocity) tuples. For example, a note
    Note(time=0, duration=4, pitch=60, velocity=64) will be encoded as a
    tuple (0, 60, 4, 64). The output shape is N * D, where N is the
    number of notes and D is 4 when `encode_velocity` is True, otherwise
    D is 3. The values of the second dimension represent time, pitch,
    duration and velocity (discarded when `encode_velocity` is False).

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to encode.
    use_start_end : bool, default: False
        Whether to use 'start' and 'end' to encode the timing rather
        than 'time' and 'duration'.
    encode_velocity : bool, default: True
        Whether to encode note velocities.
    dtype : np.dtype, type or str, default: int
        Data type of the return array.

    Returns
    -------
    ndarray, shape=(?, 3 or 4)
        Encoded array in note-based representation.

    """
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Initialize the array
    if encode_velocity:
        array = np.zeros((len(notes), 4), dtype)
    else:
        array = np.zeros((len(notes), 3), dtype)

    # Encode notes
    for i, note in enumerate(notes):
        array[i, 0] = note.time
        array[i, 1] = note.pitch
        array[i, 2] = note.end if use_start_end else note.duration
        if encode_velocity:
            if note.velocity is not None:
                array[i, 3] = note.velocity
            else:
                array[i, 3] = DEFAULT_VELOCITY

    return array
