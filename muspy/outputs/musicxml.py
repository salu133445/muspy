"""MusicXML output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union
from .music21 import to_music21
import music21

if TYPE_CHECKING:
    from ..music import Music


def write_musicxml(path: Union[str, Path], music: "Music"):
    """Write a Music object to a MusicXML file.

    Parameters
    ----------
    path : str or Path
        Path to write the MusicXML file.
    music : :class:`muspy.Music` object
        Music object to write.

    """
    stream = to_music21(music)
    musicxml_bytes = music21.musicxml.m21ToXml.GeneralObjectExporter().parse(
        stream
    )
    f = open(path, "wb")
    f.write(musicxml_bytes)
    f.close()
