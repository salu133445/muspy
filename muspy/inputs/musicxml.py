"""MusicXML input interface."""
from pathlib import Path
from typing import Union

from ..music import Music


def read_musicxml(path: Union[str, Path]) -> Music:
    """Read a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MusicXML file to be read.

    """
    # TODO: Not implemented yet
    return Music()
