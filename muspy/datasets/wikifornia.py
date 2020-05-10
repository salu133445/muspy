"""Lakh MIDI Dataset."""
from ..inputs import read_musicxml
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "Wikifornia Dataset"
_DESCRIPTION = """\
Wikifornia dataset is a collection of 6675 lead sheets in MusicMXL format. It
was originally hosted at http://www.wikifonia.org/.
"""
_HOMEPAGE = "http://www.wikifonia.org/"


class WikiforniaDataset(RemoteFolderDataset):
    """Wikifornia dataset."""

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

    @classmethod
    def _converter(cls, filename):
        return read_musicxml(filename)
