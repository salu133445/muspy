"""Note-based representation output interface."""
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from ..processor import NoteProcessor

if TYPE_CHECKING:
    from ..music import Music


def to_note_representation(music: "Music", min_step: int = 1) -> ndarray:
    """Return a Music object in note-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted note-based representation.
        size: L * D:
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
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)
    notes.sort(key=lambda x: x.start)
    processor = NoteProcessor(min_step=min_step)
    return np.array(processor.encode(notes))
