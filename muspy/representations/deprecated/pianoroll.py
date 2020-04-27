"""Utilities for pianoroll representations."""
import numpy as np
from ..processor import PianoRollProcessor


def to_pianoroll_representation(music, **kwargs):
    """Convert a :class:`muspy.Music` object to pianoroll representation.

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
            - D = 128
                the value in each dimension indicates the velocity

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
    processor = PianoRollProcessor(min_step=min_step)
    repr_seq = processor.encode(note_seq)
    return repr_seq
