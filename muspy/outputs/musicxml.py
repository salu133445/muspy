"""MusicXML output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..music import Music


def write_musicxml(music: "Music", path: Union[str, Path]):
    """Write a Music object to a MusicXML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or Path
        Path to write the MusicXML file.

    """
    pass
