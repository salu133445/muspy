"""Processor for note-based representation."""
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import Note


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
        note_repr = np.zeros((len(notes), dim), np.uint8)

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
        if not np.issubdtype(note_repr.dtype, np.integer):
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
