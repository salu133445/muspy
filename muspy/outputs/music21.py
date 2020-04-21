"""Music21 converter interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union
from music21 import stream

if TYPE_CHECKING:
    from ..music import Music


def to_music21(music: "Music"):
    """Write a Music object to a music21 stream object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    stream : :class:`stream.Stream`
        Converted music21 stream object.

    """
    # TODO: Not implemented yet
    return stream.Stream()
