"""Lakh MIDI Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_musicxml
from ..music import Music
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "Wikifonia Dataset"
_DESCRIPTION = """\
Wikifonia dataset is a collection of 6675 lead sheets in MusicMXL format. It
was originally hosted at http://www.wikifonia.org/."""
_HOMEPAGE = "http://www.wikifonia.org/"


class WikifoniaDataset(RemoteFolderDataset):
    """Wikifonia dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _sources = {
        "wikifonia": {
            "filename": "Wikifonia.zip",
            "url": "http://www.synthzone.com/files/Wikifonia/Wikifonia.zip",
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mxl"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_musicxml(filename)
