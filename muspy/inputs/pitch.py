"""Pitch-based representation input interface."""
from operator import attrgetter
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import DEFAULT_VELOCITY, Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_pitch_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_hold_state: bool = False,
    default_velocity: int = DEFAULT_VELOCITY,
) -> Music:
    """Decode pitch-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in pitch-based representation to decode.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    program : int, default: 0 (Acoustic Grand Piano)
        Program number, according to General MIDI specification [1].
        Valid values are 0 to 127.
    is_drum : bool, default: False
        Whether it is a percussion track.
    use_hold_state : bool, default: False
        Whether to use a special state for holds.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding.

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
                    time=int(start),
                    pitch=int(array[start]),
                    duration=int(end - start),
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
                time=int(start),
                pitch=int(array[start]),
                duration=int(end - start),
                velocity=default_velocity,
            )
            notes.append(note)

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
