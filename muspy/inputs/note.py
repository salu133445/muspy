"""Note-based representation input interface."""
from operator import attrgetter

import numpy as np
from numpy import ndarray

from ..classes import DEFAULT_VELOCITY, Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_note_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_start_end: bool = False,
    encode_velocity: bool = True,
    default_velocity: int = DEFAULT_VELOCITY,
) -> Music:
    """Decode note-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in note-based representation to decode.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    program : int, default: 0 (Acoustic Grand Piano)
        Program number, according to General MIDI specification [1].
        Valid values are 0 to 127.
    is_drum : bool, default: False
        Whether it is a percussion track.
    use_start_end : bool, default: False
        Whether to use 'start' and 'end' to encode the timing rather
        than 'time' and 'duration'.
    encode_velocity : bool, default: True
        Whether to encode note velocities.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding. Only used when
        `encode_velocity` is True.

    Returns
    -------
    :class:`muspy.Music`
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if not np.issubdtype(array.dtype, np.integer):
        raise TypeError("Array must be of type int.")

    notes = []
    velocity = default_velocity
    for note_tuple in array:
        if encode_velocity:
            velocity = note_tuple[3]

        if use_start_end:
            duration = note_tuple[2] - note_tuple[0]
        else:
            duration = note_tuple[2]

        notes.append(
            Note(
                time=int(note_tuple[0]),
                pitch=int(note_tuple[1]),
                duration=int(duration),
                velocity=int(velocity),
            )
        )

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
