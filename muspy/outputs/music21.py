"""Music21 converter interface."""
from typing import TYPE_CHECKING, Any

from music21.stream import Stream

if TYPE_CHECKING:
    from ..music import Music


def to_music21(music: "Music", **kwargs: Any) -> Stream:
    """Write a Music object to a music21 stream object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    stream : `music21.stream.Stream` object
        Converted music21 stream object.

    """
    raise NotImplementedError
