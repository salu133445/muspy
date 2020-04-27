"""MusicXML input interface."""
from pathlib import Path
from typing import Union

from ..music import Music
from .music21 import from_music21
import music21



def read_musicxml(path: Union[str, Path]) -> Music:
    """Read a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MusicXML file to be read.

    """
    importer = music21.musicxml.xmlToM21.MusicXMLImporter()
    importer.readFile(path)
    return from_music21(importer.stream)
