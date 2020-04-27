"""Token-based representation output interface."""
import numpy as np
from ..processor import MonoTokenProcessor


def to_monotoken_representation(music: "Music", **kwargs) -> np.ndarray:
    """Return a Music object in monotoken-based representation.

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
        Converted monotoken-based representation.
        size: L * D:
            - L for the sequence length
            - D = 1 {
                0-127: pitch onset
                128: hold state
                129: rest state
            }
        e.g.

        [C5 - - - E5 - - / G5 - - / /]
        ->
        [60, 128, 128, 128, 64, 128, 128, 129, 67, 128, 128, 129, 129]

    """
    if not music.timing.is_symbolic:
        raise Exception("object is not symbolic", music.timing)
    if len(music.tracks) != 1:
        raise Exception(
            "mono token representation can't accept more than one track!",
            len(music.tracks),
        )
    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    note_seq = music.tracks[0].notes
    note_seq.sort(key=lambda x: x.start)
    processor = MonoTokenProcessor(min_step=min_step)
    repr_seq = processor.encode(note_seq)
    return np.array(repr_seq)


def to_polytoken_representation(music: "Music", **kwargs) -> np.ndarray:
    """Return a Music object in polytoken-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted polytoken-based representation.

    """
    # TODO: Not implemented yet
    return np.array()
