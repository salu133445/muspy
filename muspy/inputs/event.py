"""Event-based representation input interface."""
from collections import defaultdict
from operator import attrgetter

import numpy as np
from numpy import ndarray

from ..classes import DEFAULT_VELOCITY, Note, Track
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
    default_velocity: int = DEFAULT_VELOCITY,
    duplicate_note_mode: str = "fifo",
) -> Music:
    """Decode event-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in event-based representation to decode.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    program : int, default: 0 (Acoustic Grand Piano)
        Program number, according to General MIDI specification [1].
        Valid values are 0 to 127.
    is_drum : bool, default: False
        Whether it is a percussion track.
    use_single_note_off_event : bool, default: False
        Whether to use a single note-off event for all the pitches. If
        True, a note-off event will close all active notes, which can
        lead to lossy conversion for polyphonic music.
    use_end_of_sequence_event : bool, default: False
        Whether to append an end-of-sequence event to the encoded
        sequence.
    max_time_shift : int, default: 100
        Maximum time shift (in ticks) to be encoded as an separate
        event. Time shifts larger than `max_time_shift` will be
        decomposed into two or more time-shift events.
    velocity_bins : int, default: 32
        Number of velocity bins to use.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding.
    duplicate_note_mode : {'fifo', 'lifo', 'all'}, default: 'fifo'
        Policy for dealing with duplicate notes. When a note off event
        is presetned while there are multiple correspoding note on
        events that have not yet been closed, we need a policy to decide
        which note on messages to close. This is only effective when
        `use_single_note_off_event` is False.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out): close the latest note on
        - 'all': close all note on messages

    Returns
    -------
    :class:`muspy.Music`
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if duplicate_note_mode.lower() not in ("fifo", "lifo", "all"):
        raise ValueError(
            "`duplicate_note_mode` must be one of 'fifo', 'lifo' and " "'all'."
        )

    # Cast the array to integer
    if not np.issubdtype(array.dtype, np.integer):
        raise TypeError("Array must be of type int.")

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
    notes = []

    # Keep track of active note on messages
    active_notes = defaultdict(list)

    # Iterate over the events
    for event in array.flatten().tolist():
        # Skip unknown events
        if event < offset_note_on or event >= vocab_size:
            continue

        # End-of-sequence events
        if use_end_of_sequence_event and event == offset_eos:
            break

        # Note on events
        if event < offset_note_off:
            pitch = event - offset_note_on
            active_notes[pitch].append(
                Note(
                    time=int(time),
                    pitch=int(pitch),
                    duration=0,
                    velocity=int(velocity),
                )
            )

        # Note off events
        elif event < offset_time_shift:
            # Close all notes
            if use_single_note_off_event:
                if active_notes:
                    for pitch, note_list in active_notes.items():
                        for note in note_list:
                            note.duration = int(time - note.time)
                            notes.append(note)
                    active_notes = defaultdict(list)
                continue

            pitch = event - offset_note_off

            # Skip it if there is no active notes
            if not active_notes[pitch]:
                continue

            # NOTE: There is no way to disambiguate duplicate notes of
            # the same pitch. Thus, we need a policy for handling
            # duplicate notes.

            # 'FIFO': (first in first out) close the earliest note
            elif duplicate_note_mode.lower() == "fifo":
                note = active_notes[pitch][0]
                note.duration = int(time - note.time)
                notes.append(note)
                del active_notes[pitch][0]

            # 'LIFO': (last in first out) close the latest note on
            elif duplicate_note_mode.lower() == "lifo":
                note = active_notes[pitch][-1]
                note.duration = int(time - note.time)
                notes.append(note)
                del active_notes[pitch][-1]

            # 'all' - close all note on events
            elif duplicate_note_mode.lower() == "all":
                for note in active_notes[pitch]:
                    note.duration = int(time - note.time)
                    notes.append(note)
                del active_notes[pitch]

        # Time-shift events
        elif event < offset_velocity:
            time += event - offset_time_shift + 1

        # Velocity events
        elif event < vocab_size:
            velocity = int((event - offset_velocity) * velocity_factor)

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
