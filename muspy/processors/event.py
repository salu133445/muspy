"""Processor for event-based representation."""
from operator import attrgetter, itemgetter
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import Note


class EventRepresentationProcessor:
    """Event-based representation processor.

    The event-based represetantion represents music as a sequence of events,
    including note-on, note-off, time-shift and velocity events. The output
    shape is M x 1, where M is the number of events. The values encode the
    events. The default configuration uses 0-127 to encode note-one events,
    128-255 for note-off events, 256-355 for time-shift events, and 356 to
    387 for velocity events.

    Attributes
    ----------
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
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    """

    def __init__(
        self,
        use_single_note_off_event: bool = False,
        use_end_of_sequence_event: bool = False,
        force_velocity_event: bool = True,
        max_time_shift: int = 100,
        velocity_bins: int = 32,
        default_velocity: int = 64,
    ):
        self.use_single_note_off_event = use_single_note_off_event
        self.use_end_of_sequence_event = use_end_of_sequence_event
        self.force_velocity_event = force_velocity_event
        self.max_time_shift = max_time_shift
        self.velocity_bins = velocity_bins
        self.default_velocity = default_velocity

        if self.use_single_note_off_event:
            self.vocab_size = 129 + self.max_time_shift + self.velocity_bins
        else:
            self.vocab_size = 256 + self.max_time_shift + self.velocity_bins
        if self.use_end_of_sequence_event:
            self.vocab_size += 1

        self._offset_note_on = 0
        self._offset_note_off = 128
        if self.use_single_note_off_event:
            self._offset_time_shift = 129
        else:
            self._offset_time_shift = 256
        self._offset_velocity = self._offset_time_shift + self.max_time_shift
        if self.use_end_of_sequence_event:
            self._offset_eos = self._offset_velocity + self.velocity_bins
        else:
            self._offset_eos = -1

    def encode(self, notes: List[Note]) -> ndarray:
        """Encode notes into event-based representation.

        Parameters
        ----------
        notes : list of :class:`muspy.Note` objects
            Note sequence to encode.

        Returns
        -------
        ndarray (np.uint16)
            Encoded array in event-based representation.

        """
        # Collect note-related events
        note_events = []
        last_velocity = -1
        for note in notes:
            # Velocity event
            if self.force_velocity_event or note.velocity != last_velocity:
                note_events.append(
                    (
                        note.time,
                        self._offset_velocity
                        + int(note.velocity * self.velocity_bins / 128),
                    )
                )
            last_velocity = note.velocity
            # Note on event
            note_events.append((note.time, self._offset_note_on + note.pitch))
            # Note off event
            if self.use_single_note_off_event:
                note_events.append((note.end, self._offset_note_off))
            else:
                note_events.append(
                    (note.end, self._offset_note_off + note.pitch)
                )

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
                div, mod = divmod(time - time_cursor, self.max_time_shift)
                for _ in range(div):
                    events.append(
                        self._offset_time_shift + self.max_time_shift - 1
                    )
                events.append(self._offset_time_shift + mod - 1)
                events.append(code)
                time_cursor = time
            else:
                events.append(code)
        # Append the end-of-sequence event
        if self.use_end_of_sequence_event:
            events.append(self._offset_eos)

        return np.array(events, np.uint16).reshape(-1, 1)

    def decode(self, event_repr: ndarray) -> List[Note]:
        """Decode event-based representation into notes.

        Parameters
        ----------
        event_repr : ndarray
            Array in event-based representation to decode. Will be casted to
            integer if not of integer type.

        Returns
        -------
        list of :class:muspy.Note objects
            Decoded notes.

        """
        if not np.issubdtype(event_repr.dtype, np.integer):
            event_repr = event_repr.astype(np.int)

        time = 0
        velocity = self.default_velocity
        velocity_factor = 128 / self.velocity_bins
        note_ons = {}
        notes = []
        for event in event_repr.flatten().tolist():
            # Skip unknown event
            if event < 0:
                continue

            # End-of-sequence event
            if self.use_end_of_sequence_event and event == self._offset_eos:
                break

            # Note on event
            if event < self._offset_note_off:
                note_ons[event] = time

            # Note off event
            elif event < self._offset_time_shift:

                # Close all notes
                if self.use_single_note_off_event:
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
                    pitch = event - self._offset_note_off
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
            elif event < self._offset_velocity:
                time += event - self._offset_time_shift + 1

            # Velocity event
            elif event < self.vocab_size:
                velocity = int(
                    (event - self._offset_velocity) * velocity_factor
                )

        notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))
        return notes
