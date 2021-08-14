"""MusicXML output interface."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Union

from music21.musicxml.archiveTools import compressXML

from .music21 import to_music21

if TYPE_CHECKING:
    from ..music import Music


def write_musicxml(
    path: Union[str, Path], music: "Music", compressed: bool = None
):
    """Write a Music object to a MusicXML file.

    Parameters
    ----------
    path : str or Path
        Path to write the MusicXML file.
    music : :class:`muspy.Music`
        Music object to write.
    compressed : bool, optional
        Whether to write to a compressed MusicXML file. If None, infer
        from the extension of the filename ('.xml' and '.musicxml' for
        an uncompressed file, '.mxl' for a compressed file).

    """
    score = to_music21(music)
    path = str(path)
    if compressed is None:
        if path.endswith((".xml", ".musicxml")):
            compressed = False
        elif path.endswith(".mxl"):
            compressed = True
        else:
            raise ValueError("Cannot infer file type from the extension.")

    if compressed:
        score.write("xml", path + ".temp.xml")
        compressXML(path + ".temp.xml", deleteOriginal=True)
        os.rename(path + ".temp.mxl", path)
    else:
        score.write("xml", path)
