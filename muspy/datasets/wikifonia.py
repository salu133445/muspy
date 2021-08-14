"""Wikifonia Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_musicxml
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

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
            "size": 35727800,
            "md5": "d26e22562e67eb7d37535e96cc5eebba",
            "sha256": "e7bce509462a73cee175308b6a3cdafa9effd6e8958b3ce03b4edb293cc6b691",
        }
    }
    _extension = "mxl"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_musicxml(filename)
