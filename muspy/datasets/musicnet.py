"""MusicNet Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "MusicNet Dataset"
_DESCRIPTION = """\
MusicNet is a collection of 330 freely-licensed classical music recordings, \
together with over 1 million annotated labels indicating the precise time of \
each note in every recording, the instrument that plays each note, and the \
note's position in the metrical structure of the composition."""
_HOMEPAGE = "https://homes.cs.washington.edu/~thickstn/musicnet.html"
_CITATION = """\
@inproceedings{thickstun2017learning,
  author={John Thickstun and Zaid Harchaoui and Sham M. Kakade},
  title={Learning Features of Music from Scratch},
  booktitle={International Conference on Learning Representations (ICLR)},
  year=2017
}"""


class MusicNetDataset(RemoteFolderDataset):
    """MusicNet Dataset (MIDI only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _citation = _CITATION
    _sources = {
        "musicnet": {
            "filename": "musicnet_midis.tar.gz",
            "url": "https://zenodo.org/record/5120004/files/musicnet_midis.tar.gz",
            "archive": True,
            "size": 2601302,
            "md5": "b5fa98a113bfc51c8a445def9f24dc7e",
            "sha256": "943cc47731ec5f397bd6fbab4dff78342472890cd484bd30ffb2e16047eef908",
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)
