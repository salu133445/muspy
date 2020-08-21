"""
Representation Processor
========================

These are classes for handling representations.

"""
from operator import attrgetter, itemgetter
from typing import List


import numpy as np
from numpy import ndarray

from .classes import Note


class NoteRepresentationProcessor:
    """Note-based representation processor.

    The note-based represetantion represents music as a sequence of (pitch,
    time, duration, velocity) tuples. For example, a note
    Note(time=0, duration=4, pitch=60, velocity=64) will be encoded as a
    tuple (0, 4, 60, 64). The output shape is L * D, where L is the number
    of notes and D is 4 when `encode_velocity` is True, otherwise D is 3.
    The values of the second dimension represent pitch, time, duration and
    velocity (discarded when `encode_velocity` is False).

    Attributes
    ----------
    use_start_end : bool
        Whether to use 'start' and 'end' to encode the timing rather than
        'time' and 'duration'. Defaults to False.
    encode_velocity : bool
        Whether to encode note velocities. Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity` is
        False. Defaults to 64.

    """

    def __init__(
        self,
        use_start_end: bool = False,
        encode_velocity: bool = True,
        default_velocity: int = 64,
    ):
        self.use_start_end = use_start_end
        self.encode_velocity = encode_velocity
        self.default_velocity = default_velocity

    def encode(self, notes: List[Note]) -> ndarray:
        """Encode notes into note-based representation.

        Parameters
        ----------
        notes : list of :class:`muspy.Note` objects
            Note sequence to encode.

        Returns
        -------
        ndarray (np.uint8)
            Encoded array in note-based representation.

        """
        dim = 4 if self.encode_velocity else 3
        note_repr = np.array((len(notes), dim), np.uint8)

        for i, note in enumerate(notes):
            note_repr[i, 0] = note.pitch
            note_repr[i, 1] = note.start if self.use_start_end else note.time
            note_repr[i, 2] = note.end if self.use_start_end else note.duration
            if self.encode_velocity:
                note_repr[i, 3] = note.velocity

        return note_repr

    def decode(self, note_repr: ndarray) -> List[Note]:
        """Decode note-based representation into notes.

        Parameters
        ----------
        note_repr : ndarray
            Array in note-based representation to decode. Will be casted to
            integer if not of integer type.

        Returns
        -------
        list of :class:muspy.Note objects
            Decoded notes.

        """
        if not issubclass(note_repr.dtype, np.integer):
            note_repr = note_repr.astype(np.int)

        notes = []
        for note_tuple in note_repr:
            if self.encode_velocity:
                velocity = note_tuple[3]
            else:
                velocity = self.default_velocity
            note = Note(
                time=note_tuple[1],
                duration=note_tuple[2] - note_tuple[1]
                if self.use_start_end
                else note_tuple[2],
                pitch=note_tuple[0],
                velocity=velocity,
            )
            notes.append(note)

        return notes


class PitchRepresentationProcessor:
    """Pitch-based representation processor.

    The pitch-based represetantion represents music as a sequence of pitch,
    rest and (optional) hold tokens. Only monophonic melodies are compatible
    with this representation. The output shape is T x 1, where T is the
    number of time steps. The values indicate whether the current time step
    is a pitch (0-127), a rest (128) or (optionally) a hold (129).

    Attributes
    ----------
    use_hold_state : bool
        Whether to use a special state for holds. Defaults to False.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    """

    def __init__(self, use_hold_state=False, default_velocity=64):
        self.use_hold_state = use_hold_state
        self.default_velocity = default_velocity

    def encode(self, notes: List[Note]) -> ndarray:
        """Encode notes into pitch-based representation.

        Parameters
        ----------
        notes : list of :class:`muspy.Note` objects
            Note sequence to encode.

        Returns
        -------
        ndarray (np.uint8)
            Encoded array in pitch-based representation.

        """
        if not notes:
            return np.zeros((1, 1), np.uint8)

        length = max((note.end for note in notes))
        pitch_repr = np.array((length, 1), np.uint8)

        # Fill the array with rests
        if self.use_hold_state:
            pitch_repr.fill(128)

        for note in notes:
            if self.use_hold_state:
                pitch_repr[note.time] = note.pitch
                pitch_repr[note.time + 1 : note.time + note.duration] = 129
            else:
                pitch_repr[note.time : note.time + note.duration] = note.pitch

        return pitch_repr

    def decode(self, pitch_repr: ndarray) -> List[Note]:
        """Decode pitch-based representation into notes.

        Parameters
        ----------
        pitch_repr : ndarray
            Array in pitch-based representation to decode. Will be casted to
            integer if not of integer type.

        Returns
        -------
        list of :class:muspy.Note objects
            Decoded notes.

        """
        if not issubclass(pitch_repr.dtype, np.integer):
            pitch_repr = pitch_repr.astype(np.int)

        notes: List[Note] = []
        diff = np.diff(pitch_repr, prepend=-1, append=-1)
        boundaries = np.nonzero(diff)[0]
        if self.use_hold_state:
            is_awaiting_hold = False
            for start, end in zip(boundaries[:-1], boundaries[1:]):
                # Rest
                if pitch_repr[start] == 129:
                    is_awaiting_hold = False
                    continue

                # Hold
                if pitch_repr[start] == 128:
                    # Skip a hold that does not follow any pitch
                    if not is_awaiting_hold:
                        continue

                    notes[-1].duration += end - start
                    is_awaiting_hold = False

                # Pitch
                else:
                    note = Note(
                        time=start - 1,
                        duration=end - start + 1,
                        pitch=pitch_repr[start],
                        velocity=self.default_velocity,
                    )
                    notes.append(note)
                    is_awaiting_hold = True

        else:
            for start, end in zip(boundaries[:-1], boundaries[1:]):
                # Rest
                if pitch_repr[start] != 128:
                    continue

                # Pitch
                note = Note(
                    time=start,
                    duration=end - start,
                    pitch=pitch_repr[start],
                    velocity=self.default_velocity,
                )
                notes.append(note)

        return notes


class EventRepresentationProcessor:
    """Event-based representation processor.

    Representation Format:
    -----
    Size: L * D:
        - L for the sequence (event) length
        - D = 1 {
            0-127: note-on event,
            128-255: note-off event,
            256-355(default):
                tick-shift event
                256 for one tick, 355 for 100 ticks
                the maximum number of tick-shift can be specified
            356-388 (default):
                velocity event
                the maximum number of quantized velocity can be specified
            }

    Parameters:
    -----
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)
    tick_dim(optional):
        tick-shift event dimensions
        the maximum number of tick-shift (default = 100)
    velocity_dim(optional):
        velocity event dimensions
        the maximum number of quantized velocity (default = 32, max = 128)

    e.g.

    [C5 - - - E5 - - / G5 - - / /]
    ->
    [380, 60, 259, 188, 64, 258, 192, 256, 67, 258, 195, 257]

    """

    def __init__(
        self,
        max_tick_shifts: int = 100,
        velocity_bins: int = 32,
        use_single_note_off_event: bool = False,
        default_velocity: int = 64,
    ):
        self.max_tick_shifts = max_tick_shifts
        self.velocity_bins = velocity_bins
        self.use_single_note_off_event = use_single_note_off_event
        self.default_velocity = default_velocity

        if self.use_single_note_off_event:
            self.vocab_size = 129 + self.max_tick_shifts + self.velocity_bins
        else:
            self.vocab_size = 256 + self.max_tick_shifts + self.velocity_bins

        self._offset_note_on = 0
        self._offset_note_off = 128
        if self.use_single_note_off_event:
            self._offset_time_shift = 129
        else:
            self._offset_time_shift = 256
        self._offset_velocity = self._offset_time_shift + self.max_tick_shifts

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
        for note in notes:
            # Velocity event
            note_events.append(
                (
                    note.time,
                    self._offset_velocity
                    + note.velocity * self.velocity_bins / 128,
                )
            )
            # Note on event
            note_events.append((note.time, self._offset_note_on + note.pitch))
            # Note off event
            if self.use_single_note_off_event:
                note_events.append((note.time, self._offset_note_off))
            else:
                note_events.append(
                    (note.time, self._offset_note_off + note.pitch)
                )

        # Sort events by time
        note_events.sort(key=itemgetter(0))

        # Create a list for all events
        events = []
        # Initialize the time cursor
        time = 0
        # Iterate over note events
        for note_event in note_events:
            # If event time is after the time cursor, append tick shift events
            if note_event[0] > time:
                div, mod = divmod(note_event[0] - time, self.max_tick_shifts)
                for _ in range(div):
                    events.append(
                        self._offset_time_shift + self.max_tick_shifts - 1
                    )
                events.append(self._offset_time_shift + mod - 1)

            else:
                events.append(note_event[1])

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
        time = 0
        velocity = self.default_velocity
        note_ons = {}
        notes = []
        for event in event_repr:
            # Skip unknown event
            if event < 0:
                continue

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

                # Close a specific note
                else:
                    pitch = event - self._offset_note_off
                    onset = note_ons.get(pitch)
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
                time += event - self._offset_time_shift

            # Velocity event
            elif event < self.vocab_size:
                velocity = event - self._offset_velocity

        notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))
        return notes


class PianoRollProcessor:
    """Piano-roll representation processor.

    The piano-roll represetantion represents music as a time-pitch matrix,
    where the columns are the time steps and the rows are the pitches. The
    values indicate the presence of pitches at different time steps. The
    output shape is T x 128, where T is the number of time steps.

    Attributes
    ----------
    encode_velocity : bool
        Whether to encode velocities. If True, a binary-valued array will be
        return. Otherwise, an integer array will be return. Defaults to
        False.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity` is
        False. Defaults to 64.

    """

    def __init__(
        self, encode_velocity: bool = True, default_velocity: int = 64
    ):
        self.encode_velocity = encode_velocity
        self.default_velocity = default_velocity

    def encode(self, notes: List[Note]) -> ndarray:
        """Encode notes into piano-roll representation.

        Parameters
        ----------
        notes : list of :class:`muspy.Note` objects
            Note sequence to encode.

        Returns
        -------
        ndarray (np.uint8 or np.bool)
            Encoded array in piano-roll representation.

        """
        if not notes:
            return np.zeros((1, 128), np.uint8)

        length = max((note.end for note in notes))
        pianoroll = np.zeros((length + 1, 128), np.uint8)

        for note in notes:
            pianoroll[note.time : note.end, note.pitch] = (
                note.velocity if self.encode_velocity else (note.velocity > 0)
            )
        return pianoroll

    def decode(self, pianoroll: ndarray) -> List[Note]:
        """Decode piano-roll representation into notes.

        Parameters
        ----------
        pianoroll : ndarray
            Array in piano-roll representation to decode. Will be casted to
            integer if not of integer type.

        Returns
        -------
        list of :class:muspy.Note objects
            Decoded notes.

        """
        if self.encode_velocity and not issubclass(
            pianoroll.dtype, np.integer
        ):
            pianoroll = pianoroll.astype(np.int)
        elif not self.encode_velocity and not issubclass(
            pianoroll.dtype, np.bool
        ):
            pianoroll = pianoroll.astype(np.bool)

        binarized = pianoroll > 0

        diff = np.diff(binarized, axis=0, prepend=0, append=0)
        notes = []
        for i in range(128):
            boundaries = np.nonzero(diff[:, i])[0]
            for note_idx in range(len(boundaries) // 2):
                start = boundaries[2 * note_idx]
                end = boundaries[2 * note_idx + 1]
                if self.encode_velocity:
                    velocity = pianoroll[start, i]
                else:
                    velocity = self.default_velocity
                note = Note(
                    time=start,
                    duration=end - start,
                    pitch=i,
                    velocity=velocity,
                )
                notes.append(note)

        notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))
        return notes
