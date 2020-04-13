"""MusicXML I/O utilities."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..music import Music


def read_musicxml(path: Union[str, Path]) -> "Music":
    """Read a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the MusicXML file to be read.

    """
    music = Music()
    # TODO: Not implemented yet
    return music


def write_musicxml(music: "Music", path: Union[str, Path]):
    """Write a Music object to a MusicXML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or :class:`pathlib.Path`
        Path to write the MusicXML file.

    """
    pass
