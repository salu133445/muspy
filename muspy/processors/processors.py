from typing import Union

import numpy as np
from numpy import ndarray

from ..inputs import (
    from_note_representation,
    from_pianoroll_representation,
    from_pitch_representation,
)
from ..music import Music
from ..outputs import (
    to_note_representation,
    to_pianoroll_representation,
    to_pitch_representation,
)

__all__ = [
    "NoteRepresentationProcessor",
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
    use_start_end : bool
        Whether to use 'start' and 'end' to encode the timing rather
        than 'time' and 'duration'. Defaults to False.
    encode_velocity : bool
        Whether to encode note velocities. Defaults to True.
    dtype : dtype, type or str
        Data type of the return array. Defaults to int.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity`
        is False. Defaults to 64.

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


class PitchRepresentationProcessor:
    """Pitch-based representation processor.

    The pitch-based represetantion represents music as a sequence of
    pitch, rest and (optional) hold tokens. Only monophonic melodies are
    compatible with this representation. The output shape is T x 1,
    where T is the number of time steps. The values indicate whether the
    current time step is a pitch (0-127), a rest (128) or (optionally) a
    hold (129).

    Attributes
    ----------
    use_hold_state : bool
        Whether to use a special state for holds. Defaults to False.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

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
    encode_velocity : bool
        Whether to encode velocities. If True, a binary-valued array
        will be return. Otherwise, an integer array will be return.
        Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity`
        is False. Defaults to 64.

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
