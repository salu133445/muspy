"""Music21 input interface."""
from pathlib import Path
from typing import Union

from ..music import Music
from music21 import stream


def from_music21(stream: stream.Stream) -> Music:
    """Convert a music21 object into a Music object.

    Parameters
    ----------
    stream : stream.Stream
        a music21 object to be converted.

    """
    # TODO: Not implemented yet
    return Music()
