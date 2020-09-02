"""Note-based representation input interface."""
from operator import attrgetter

import numpy as np
from numpy import ndarray

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_note_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_start_end: bool = False,
    encode_velocity: bool = True,
    default_velocity: int = 64,
) -> Music:
    """Decode note-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in note-based representation to decode. Will be casted to
        integer if not of integer type.
    resolution : int
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    program : int, optional
        Program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand
        Piano).
    is_drum : bool, optional
        A boolean indicating if it is a percussion track. Defaults to
        False.
    use_start_end : bool
        Whether to use 'start' and 'end' to encode the timing rather than
        'time' and 'duration'. Defaults to False.
    encode_velocity : bool
        Whether to encode note velocities. Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity` is
        False. Defaults to 64.

    Returns
    -------
    :class:`muspy.Music` object
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if not np.issubdtype(array.dtype, np.integer):
        array = array.astype(np.int)

    notes = []
    velocity = default_velocity
    for note_tuple in array:
        if encode_velocity:
            velocity = note_tuple[3]
        note = Note(
            time=note_tuple[1],
            duration=note_tuple[2] - note_tuple[1]
            if use_start_end
            else note_tuple[2],
            pitch=note_tuple[0],
            velocity=velocity,
        )
        notes.append(note)

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
