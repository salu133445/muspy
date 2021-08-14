"""Representation processors.

This module defines the processors for commonly used representations.

Classes
-------

- NoteRepresentationProcessor
- EventRepresentationProcessor
- PianoRollRepresentationProcessor
- PitchRepresentationProcessor

"""
from typing import Union

import numpy as np
from numpy import ndarray

from .inputs import (
    from_event_representation,
    from_note_representation,
    from_pianoroll_representation,
    from_pitch_representation,
)
from .music import Music
from .outputs import (
    to_event_representation,
    to_note_representation,
    to_pianoroll_representation,
    to_pitch_representation,
)

__all__ = [
    "NoteRepresentationProcessor",
    "EventRepresentationProcessor",
    "PianoRollRepresentationProcessor",
    "PitchRepresentationProcessor",
]


class NoteRepresentationProcessor:
    """Note-based representation processor.

    The note-based represetantion represents music as a sequence of
    (pitch, time, duration, velocity) tuples. For example, a note
    Note(time=0, duration=4, pitch=60, velocity=64) will be encoded as a
    tuple (0, 4, 60, 64). The output shape is L * D, where L is th
    number of notes and D is 4 when `encode_velocity` is True, otherwise
    D is 3. The values of the second dimension represent pitch, time,
    duration and velocity (discarded when `encode_velocity` is False).

    Attributes
    ----------
    use_start_end : bool, default: False
        Whether to use 'start' and 'end' to encode the timing rather
        than 'time' and 'duration'.
    encode_velocity : bool, default: True
        Whether to encode note velocities.
    dtype : dtype, type or str, default: int
        Data type of the return array.
    default_velocity : int, default: 64
        Default velocity value to use when decoding if `encode_velocity`
        is False.

    """

    def __init__(
        self,
        use_start_end: bool = False,
        encode_velocity: bool = True,
        dtype: Union[np.dtype, type, str] = int,
        default_velocity: int = 64,
    ):
        self.use_start_end = use_start_end
        self.encode_velocity = encode_velocity
        self.dtype = dtype
        self.default_velocity = default_velocity

    def encode(self, music: Music) -> ndarray:
        """Encode a Music object into note-based representation.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        ndarray (np.uint8)
            Encoded array in note-based representation.

        See Also
        --------
        :func:`muspy.to_note_representation` :
            Convert a Music object into note-based representation.

        """
        return to_note_representation(
            music,
            use_start_end=self.use_start_end,
            encode_velocity=self.encode_velocity,
            dtype=self.dtype,
        )

    def decode(self, array: ndarray) -> Music:
        """Decode note-based representation into a Music object.

        Parameters
        ----------
        array : ndarray
            Array in note-based representation to decode. Cast to
            integer if not of integer type.

        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.

        See Also
        --------
        :func:`muspy.from_note_representation` :
            Return a Music object converted from note-based
            representation.

        """
        return from_note_representation(
            array,
            use_start_end=self.use_start_end,
            encode_velocity=self.encode_velocity,
            default_velocity=self.default_velocity,
        )


class EventRepresentationProcessor:
    """Event-based representation processor.

    The event-based represetantion represents music as a sequence of
    events, including note-on, note-off, time-shift and velocity events.
    The output shape is M x 1, where M is the number of events. The
    values encode the events. The default configuration uses 0-127 to
    encode note-one events, 128-255 for note-off events, 256-355 for
    time-shift events, and 356 to 387 for velocity events.

    Attributes
    ----------
    use_single_note_off_event : bool, default: False
        Whether to use a single note-off event for all the pitches. If
        True, the note-off event will close all active notes, which can
        lead to lossy conversion for polyphonic music.
    use_end_of_sequence_event : bool, default: False
        Whether to append an end-of-sequence event to the encoded
        sequence.
    encode_velocity : bool, default: False
        Whether to encode velocities.
    force_velocity_event : bool, default: True
        Whether to add a velocity event before every note-on event. If
        False, velocity events are only used when the note velocity is
        changed (i.e., different from the previous one).
    max_time_shift : int, default: 100
        Maximum time shift (in ticks) to be encoded as an separate
        event. Time shifts larger than `max_time_shift` will be
        decomposed into two or more time-shift events.
    velocity_bins : int, default: 32
        Number of velocity bins to use.
    default_velocity : int, default: 64
        Default velocity value to use when decoding.

    """

    def __init__(
        self,
        use_single_note_off_event: bool = False,
        use_end_of_sequence_event: bool = False,
        encode_velocity: bool = False,
        force_velocity_event: bool = True,
        max_time_shift: int = 100,
        velocity_bins: int = 32,
        default_velocity: int = 64,
    ):
        self.use_single_note_off_event = use_single_note_off_event
        self.use_end_of_sequence_event = use_end_of_sequence_event
        self.encode_velocity = encode_velocity
        self.force_velocity_event = force_velocity_event
        self.max_time_shift = max_time_shift
        self.velocity_bins = velocity_bins
        self.default_velocity = default_velocity

    def encode(self, music: Music) -> ndarray:
        """Encode a Music object into event-based representation.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        ndarray (np.uint16)
            Encoded array in event-based representation.

        See Also
        --------
        :func:`muspy.to_event_representation` :
            Convert a Music object into event-based representation.

        """
        return to_event_representation(
            music,
            use_single_note_off_event=self.use_single_note_off_event,
            use_end_of_sequence_event=self.use_end_of_sequence_event,
            encode_velocity=self.encode_velocity,
            force_velocity_event=self.force_velocity_event,
            max_time_shift=self.max_time_shift,
            velocity_bins=self.velocity_bins,
        )

    def decode(self, array: ndarray) -> Music:
        """Decode event-based representation into a Music object.

        Parameters
        ----------
        array : ndarray
            Array in event-based representation to decode. Cast to
            integer if not of integer type.

        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.

        See Also
        --------
        :func:`muspy.from_event_representation` :
            Return a Music object converted from event-based
            representation.

        """
        return from_event_representation(
            array,
            use_single_note_off_event=self.use_single_note_off_event,
            use_end_of_sequence_event=self.use_end_of_sequence_event,
            max_time_shift=self.max_time_shift,
            velocity_bins=self.velocity_bins,
            default_velocity=self.default_velocity,
        )


class PitchRepresentationProcessor:
    """Pitch-based representation processor.

    The pitch-based represetantion represents music as a sequence of
    pitch, rest and (optional) hold tokens. Only monophonic melodies are
    compatible with this representation. The output shape is T x 1,
    where T is the number of time steps. The values indicate whether the
    current time step is a pitch (0-127), a rest (128) or, optionally, a
    hold (129).

    Attributes
    ----------
    use_hold_state : bool, default: False
        Whether to use a special state for holds.
    default_velocity : int, default: 64
        Default velocity value to use when decoding.

    """

    def __init__(
        self, use_hold_state: bool = False, default_velocity: int = 64,
    ):
        self.use_hold_state = use_hold_state
        self.default_velocity = default_velocity

    def encode(self, music: Music) -> ndarray:
        """Encode a Music object into pitch-based representation.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        ndarray (np.uint8)
            Encoded array in pitch-based representation.

        See Also
        --------
        :func:`muspy.to_pitch_representation` :
            Convert a Music object into pitch-based representation.

        """
        return to_pitch_representation(
            music, use_hold_state=self.use_hold_state
        )

    def decode(self, array: ndarray) -> Music:
        """Decode pitch-based representation into a Music object.

        Parameters
        ----------
        array : ndarray
            Array in pitch-based representation to decode. Cast to
            integer if not of integer type.

        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.

        See Also
        --------
        :func:`muspy.from_pitch_representation` :
            Return a Music object converted from pitch-based
            representation.

        """
        return from_pitch_representation(
            array,
            use_hold_state=self.use_hold_state,
            default_velocity=self.default_velocity,
        )


class PianoRollRepresentationProcessor:
    """Piano-roll representation processor.

    The piano-roll represetantion represents music as a time-pitch
    matrix, where the columns are the time steps and the rows are the
    pitches. The values indicate the presence of pitches at different
    time steps. The output shape is T x 128, where T is the number of
    time steps.

    Attributes
    ----------
    encode_velocity : bool, default: True
        Whether to encode velocities. If True, a binary-valued array
        will be return. Otherwise, an integer array will be return.
    default_velocity : int, default: 64
        Default velocity value to use when decoding if `encode_velocity`
        is False.

    """

    def __init__(
        self, encode_velocity: bool = True, default_velocity: int = 64,
    ):
        self.encode_velocity = encode_velocity
        self.default_velocity = default_velocity

    def encode(self, music: Music) -> ndarray:
        """Encode a Music object into piano-roll representation.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        ndarray (np.uint8)
            Encoded array in piano-roll representation.

        See Also
        --------
        :func:`muspy.to_pianoroll_representation` :
            Convert a Music object into piano-roll representation.

        """
        return to_pianoroll_representation(
            music, encode_velocity=self.encode_velocity
        )

    def decode(self, array: ndarray) -> Music:
        """Decode piano-roll representation into a Music object.

        Parameters
        ----------
        array : ndarray
            Array in piano-roll representation to decode. Cast to
            integer if not of integer type. If `encode_velocity` is
            True, casted to boolean if not of boolean type.

        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.

        See Also
        --------
        :func:`muspy.from_pianoroll_representation` :
            Return a Music object converted from piano-roll
            representation.

        """
        return from_pianoroll_representation(
            array,
            encode_velocity=self.encode_velocity,
            default_velocity=self.default_velocity,
        )
