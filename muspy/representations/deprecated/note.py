"""Utilities for note-based representations."""

import numpy as np
from .processor import NoteProcessor


def to_note_representation(music, **kwargs):
    """Convert a :class:`muspy.Music` object to a note-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    ----------
    repr_seq:
        the note representation tokens
        Size: L * D:
            - L for the sequence (note) length
            - D = 4 {
                pitch: 0 - 127,
                start: start ticks,
                end: end ticks,
                velocity: 0 - 100
            }
        e.g.  [C5 - - - E5 - - / G5 - - / /]
        -> [[60, 0, 3, 100], [64, 3, 5, 100], [67, 6, 8, 100]]
        (assume velocity to be 100)

    """

    if not music.timing.is_symbolic:
        raise Exception("object is not symbolic", music.timing)
    note_seq = []
    for track in music.tracks:
        note_seq.extend(track.notes)

    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    note_seq.sort(key=lambda x: x.start)
    processor = NoteProcessor(min_step=min_step)
    repr_seq = processor.encode(note_seq)
    return np.array(repr_seq)
