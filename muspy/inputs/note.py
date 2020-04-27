"""Note-based representation input interface."""
from ..classes import Track
from ..music import Music
from ..processor import NoteProcessor


def from_note_representation(data, **kwargs) -> Music:
    """Return a Music object converted from a note-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in note-based representation to be converted.
        size: L * D:
                    - L for the sequence (note) length
                    - D = 4 {
                        pitch: 0 - 127,
                        start: start ticks,
                        end: end ticks,
                        velocity: 0 - 100
                    }
                e.g. [[60, 0, 3, 100], [64, 3, 5, 100], [67, 6, 8, 100]] 
                -> [C5 - - - E5 - - / G5 - - / /]
                (assume velocity to be 100)
    min_step(optional):
        minimum quantification step
        decide how many ticks (in notes) to be the basic unit (in data) (default = 1)


    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object. (Only Track - Note has the information)

    """
    repr_seq = list(data)
    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    processor = NoteProcessor(min_step=min_step)
    note_seq = processor.decode(repr_seq)
    return Music(tracks = [Track(notes = note_seq)])