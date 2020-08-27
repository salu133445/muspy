"""Processor for piano-roll representation."""
from operator import attrgetter
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import Note


class PianoRollRepresentationProcessor:
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
        if self.encode_velocity:
            pianoroll = np.zeros((length + 1, 128), np.uint8)
        else:
            pianoroll = np.zeros((length + 1, 128), np.bool)

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
        if self.encode_velocity and not np.issubdtype(
            pianoroll.dtype, np.integer
        ):
            pianoroll = pianoroll.astype(np.int)
        elif not self.encode_velocity and not np.issubdtype(
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
