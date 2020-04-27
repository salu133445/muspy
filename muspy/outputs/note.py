"""Note-based representation output interface."""
import numpy as np
from ..processor import NoteProcessor


def to_note_representation(music: "Music", **kwargs) -> np.ndarray:
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
    # TODO: Not implemented yet
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
