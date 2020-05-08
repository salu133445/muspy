"""Music21 input interface."""
from music21.stream import Stream

from ..music import Music


def from_music21(stream: Stream) -> Music:
    """Convert a music21 object into a Music object.

    Parameters
    ----------
    stream : stream.Stream
        a music21 object to be converted.

    """
    raise NotImplementedError
