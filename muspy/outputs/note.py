"""Note-based representation output interface."""
from operator import attrgetter
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from ..classes import DEFAULT_VELOCITY
from ..utils import rencode_tempo

if TYPE_CHECKING:
    from ..music import Music


def to_note_representation(
    music: "Music", use_start_end: bool = False, encode_velocity: bool = True, encode_tempo: bool = True
) -> ndarray:
    """Encode a Music object into note-based representation.

    The note-based represetantion represents music as a sequence of (time,
    pitch, duration, velocity, tempo) tuples. For example, a note
    Note(time=0, duration=4, pitch=60, velocity=64, tempo=86) will be encoded as a
    tuple (0, 60, 4, 64, 86). The output shape is N * D, where N is the number
    of notes and D is 5 when both `encode_velocity` and `encode_tempo` is True, D is 4
    when either `encode_velocity` or `encode_tempo` is True, otherwise D is 3.
    The values of the second dimension represent time, pitch, duration and
    velocity(discarded when `encode_velocity` is False), tempo (discarded when `encode_tempo` is False).
    if `encode_velocity` and `encode_tempo` is True, a note will be encoded as
    (time, duration, pitch, velocity, tempo), if either `encode_tempo` or `encode_velocity` is True,
    a note will be encoded as (time, duration, pitch, velocity/tempo), else it
    will be encoded as (time, duration, pitch)

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to encode.
    use_start_end : bool
        Whether to use 'start' and 'end' to encode the timing rather than
        'time' and 'duration'. Defaults to False.
    encode_velocity : bool
        Whether to encode note velocities. Defaults to True.
    encode_tempo : bool
        Whether to encode note tempo. Defaults to True.
    Returns
    -------
    ndarray, dtype=uint8, shape=(?, 3 or 4)
        Encoded array in note-based representation.

    """
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)
    tempos = rencode_tempo(music.tempos, music.get_end_time())
    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Initialize the array
    if encode_velocity and encode_tempo:
        array = np.zeros((len(notes), 5), np.uint32)
    elif encode_tempo or encode_velocity:
        array = np.zeros((len(notes), 4), np.uint32)
    else:
        array = np.zeros((len(notes), 3), np.uint32)

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
        if encode_tempo and encode_velocity:
            array[i, 4] = tempos[note.time]
        elif encode_tempo and not encode_velocity:
            array[i, 3] = tempos[note.time]

    return array
