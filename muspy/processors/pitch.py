"""Processor for pitch-based representation."""
from typing import List

import numpy as np
from numpy import ndarray

from ..classes import Note


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
        pitch_repr = np.zeros((length, 1), np.uint8)

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
        if not np.issubdtype(pitch_repr.dtype, np.integer):
            pitch_repr = pitch_repr.astype(np.int)

        notes: List[Note] = []
        diff = np.diff(pitch_repr.flatten(), prepend=-1, append=-1)
        boundaries = np.nonzero(diff)[0]
        if self.use_hold_state:
            is_awaiting_hold = False
            for start, end in zip(boundaries[:-1], boundaries[1:]):
                # Rest
                if pitch_repr[start] == 128:
                    is_awaiting_hold = False
                    continue

                # Hold
                if pitch_repr[start] == 129:
                    # Skip a hold that does not follow any pitch
                    if not is_awaiting_hold:
                        continue

                    notes[-1].duration += end - start
                    is_awaiting_hold = False

                # Pitch
                else:
                    note = Note(
                        time=start,
                        duration=end - start,
                        pitch=pitch_repr[start],
                        velocity=self.default_velocity,
                    )
                    notes.append(note)
                    is_awaiting_hold = True

        else:
            for start, end in zip(boundaries[:-1], boundaries[1:]):
                # Rest
                if pitch_repr[start] == 128:
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
