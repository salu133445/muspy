"""Pitch-based representation input interface."""
from operator import attrgetter
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_pitch_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_hold_state: bool = False,
    default_velocity: int = 64,
) -> Music:
    """Decode pitch-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in pitch-based representation to decode. Will be casted to
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
    use_hold_state : bool
        Whether to use a special state for holds. Defaults to False.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    Returns
    -------
    :class:`muspy.Music` object
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    # Cast the array to integer
    if not np.issubdtype(array.dtype, np.integer):
        array = array.astype(np.int)

    # Find the note boundaries
    notes: List[Note] = []
    diff = np.diff(array.flatten(), prepend=-1, append=-1)
    boundaries = np.nonzero(diff)[0]

    # Decode pitches
    if use_hold_state:
        is_awaiting_hold = False
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            # Skip rests
            if array[start] == 128:
                is_awaiting_hold = False
                continue

            # Hold
            if array[start] == 129:
                # Skip a hold that does not follow any pitch
                if not is_awaiting_hold:
                    continue

                notes[-1].duration += end - start
                is_awaiting_hold = False

            # Pitch
            else:
                note = Note(
                    time=start,
                    duration=end - start,
                    pitch=array[start],
                    velocity=default_velocity,
                )
                notes.append(note)
                is_awaiting_hold = True

    else:
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            # Skip rests
            if array[start] == 128:
                continue

            # Pitch
            note = Note(
                time=start,
                duration=end - start,
                pitch=array[start],
                velocity=default_velocity,
            )
            notes.append(note)

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
