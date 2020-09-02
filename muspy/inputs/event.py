"""Event-based representation input interface."""
from operator import attrgetter

import numpy as np
from numpy import ndarray

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


def from_event_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_single_note_off_event: bool = False,
    use_end_of_sequence_event: bool = False,
    max_time_shift: int = 100,
    velocity_bins: int = 32,
    default_velocity: int = 64,
) -> Music:
    """Decode event-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in event-based representation to decode. Will be casted to
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
    use_single_note_off_event : bool
        Whether to use a single note-off event for all the pitches. If True,
        the note-off event will close all active notes, which can lead to
        lossy conversion for polyphonic music. Defaults to False.
    use_end_of_sequence_event : bool
        Whether to append an end-of-sequence event to the encoded sequence.
        Defaults to False.
    max_time_shift : int
        Maximum time shift (in ticks) to be encoded as an separate event.
        Time shifts larger than `max_time_shift` will be decomposed into
        two or more time-shift events. Defaults to 100.
    velocity_bins : int
        Number of velocity bins to use. Defaults to 32.
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

    # Compute offsets
    offset_note_on = 0
    offset_note_off = 128
    offset_time_shift = 129 if use_single_note_off_event else 256
    offset_velocity = offset_time_shift + max_time_shift
    if use_end_of_sequence_event:
        offset_eos = offset_velocity + velocity_bins

    # Compute vocabulary size
    if use_single_note_off_event:
        vocab_size = 129 + max_time_shift + velocity_bins
    else:
        vocab_size = 256 + max_time_shift + velocity_bins
    if use_end_of_sequence_event:
        vocab_size += 1

    # Decode events
    time = 0
    velocity = default_velocity
    velocity_factor = 128 / velocity_bins
    note_ons = {}
    notes = []
    for event in array.flatten().tolist():
        # Skip unknown event
        if event < offset_note_on:
            continue

        # End-of-sequence event
        if use_end_of_sequence_event and event == offset_eos:
            break

        # Note on event
        if event < offset_note_off:
            note_ons[event] = time

        # Note off event
        elif event < offset_time_shift:

            # Close all notes
            if use_single_note_off_event:
                for pitch, note_on in note_ons.items():
                    note = Note(
                        time=note_on,
                        duration=time - note_on,
                        pitch=pitch,
                        velocity=velocity,
                    )
                    notes.append(note)
                note_ons = {}

            # Close a specific note
            else:
                pitch = event - offset_note_off
                onset = note_ons.pop(pitch)
                if onset is not None:
                    note = Note(
                        time=onset,
                        duration=time - onset,
                        pitch=pitch,
                        velocity=velocity,
                    )
                    notes.append(note)

        # Time shift event
        elif event < offset_velocity:
            time += event - offset_time_shift + 1

        # Velocity event
        elif event < vocab_size:
            velocity = int((event - offset_velocity) * velocity_factor)

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
