"""Event-based representation output interface."""
from operator import attrgetter, itemgetter
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

if TYPE_CHECKING:
    from ..music import Music


def to_event_representation(
    music: "Music",
    use_single_note_off_event: bool = False,
    use_end_of_sequence_event: bool = False,
    force_velocity_event: bool = True,
    max_time_shift: int = 100,
    velocity_bins: int = 32,
) -> ndarray:
    """Encode a Music object into event-based representation.

    The event-based represetantion represents music as a sequence of events,
    including note-on, note-off, time-shift and velocity events. The output
    shape is M x 1, where M is the number of events. The values encode the
    events. The default configuration uses 0-127 to encode note-one events,
    128-255 for note-off events, 256-355 for time-shift events, and 356 to
    387 for velocity events.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to encode.
    use_single_note_off_event : bool
        Whether to use a single note-off event for all the pitches. If True,
        the note-off event will close all active notes, which can lead to
        lossy conversion for polyphonic music. Defaults to False.
    use_end_of_sequence_event : bool
        Whether to append an end-of-sequence event to the encoded sequence.
        Defaults to False.
    force_velocity_event : bool
        Whether to add a velocity event before every note-on event. If
        False, velocity events are only used when the note velocity is
        changed (i.e., different from the previous one). Defaults to True.
    max_time_shift : int
        Maximum time shift (in ticks) to be encoded as an separate event.
        Time shifts larger than `max_time_shift` will be decomposed into
        two or more time-shift events. Defaults to 100.
    velocity_bins : int
        Number of velocity bins to use. Defaults to 32.

    Returns
    -------
    ndarray, dtype=uint16, shape=(?, 1)
        Encoded array in event-based representation.

    """
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes and not use_end_of_sequence_event:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Compute offsets
    offset_note_on = 0
    offset_note_off = 128
    offset_time_shift = 129 if use_single_note_off_event else 256
    offset_velocity = offset_time_shift + max_time_shift
    if use_end_of_sequence_event:
        offset_eos = offset_velocity + velocity_bins

    # Collect note-related events
    note_events = []
    last_velocity = -1
    for note in notes:
        # Velocity event
        if force_velocity_event or note.velocity != last_velocity:
            note_events.append(
                (
                    note.time,
                    offset_velocity + int(note.velocity * velocity_bins / 128),
                )
            )
        last_velocity = note.velocity
        # Note on event
        note_events.append((note.time, offset_note_on + note.pitch))
        # Note off event
        if use_single_note_off_event:
            note_events.append((note.end, offset_note_off))
        else:
            note_events.append((note.end, offset_note_off + note.pitch))

    # Sort events by time
    note_events.sort(key=itemgetter(0))

    # Create a list for all events
    events = []
    # Initialize the time cursor
    time_cursor = 0
    # Iterate over note events
    for time, code in note_events:
        # If event time is after the time cursor, append tick shift events
        if time > time_cursor:
            div, mod = divmod(time - time_cursor, max_time_shift)
            for _ in range(div):
                events.append(offset_time_shift + max_time_shift - 1)
            events.append(offset_time_shift + mod - 1)
            events.append(code)
            time_cursor = time
        else:
            events.append(code)
    # Append the end-of-sequence event
    if use_end_of_sequence_event:
        events.append(offset_eos)

    return np.array(events, np.uint16).reshape(-1, 1)
