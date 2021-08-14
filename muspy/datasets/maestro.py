"""MAESTRO Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "MAESTRO Dataset"
_DESCRIPTION = """\
MAESTRO (MIDI and Audio Edited for Synchronous TRacks and Organization) is a \
dataset composed of over 200 hours of virtuosic piano performances captured \
with fine alignment (~3 ms) between note labels and audio waveforms."""
_HOMEPAGE = "https://magenta.tensorflow.org/datasets/maestro"
_LICENSE = "Creative Commons Attribution Non-Commercial Share-Alike 4.0 \
(CC BY-NC-SA 4.0)"
_CITATION = """\
@inproceedings{hawthorne2018enabling,
  title={Enabling Factorized Piano Music Modeling and Generation with the {MAESTRO} Dataset},
  author={Curtis Hawthorne and Andriy Stasyuk and Adam Roberts and Ian Simon and Cheng-Zhi Anna Huang and Sander Dieleman and Erich Elsen and Jesse Engel and Douglas Eck},
  booktitle={Proceedings of the 7th International Conference on Learning Representations (ICLR)},
  year=2019,
  url={https://openreview.net/forum?id=r1lYRjC9F7}
}"""


class MAESTRODatasetV1(RemoteFolderDataset):
    """MAESTRO Dataset V1 (MIDI only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "maestro": {
            "filename": "maestro-v1.0.0-midi.zip",
            "url": "https://storage.googleapis.com/magentadata/datasets/maestro/v1.0.0/maestro-v1.0.0-midi.zip",
            "archive": True,
            "size": 46579421,
            "sha256": "f620f9e1eceaab8beea10617599add2e9c83234199b550382a2f603098ae7135",
        }
    }
    _extension = "midi"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)


class MAESTRODatasetV2(RemoteFolderDataset):
    """MAESTRO Dataset V2 (MIDI only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "maestro": {
            "filename": "maestro-v2.0.0-midi.zip",
            "url": "https://storage.googleapis.com/magentadata/datasets/maestro/v2.0.0/maestro-v2.0.0-midi.zip",
            "archive": True,
            "size": 59243107,
            "sha256": "ec2cc9d94886c6b376db1eaa2b8ad1ce62ff9f0a28b3744782b13163295dadf3",
        }
    }
    _extension = "midi"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)


class MAESTRODatasetV3(RemoteFolderDataset):
    """MAESTRO Dataset V3 (MIDI only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "maestro": {
            "filename": "maestro-v3.0.0-midi.zip",
            "url": "https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip",
            "archive": True,
            "size": 58416533,
            "sha256": "70470ee253295c8d2c71e6d9d4a815189e35c89624b76d22fce5a019d5dde12c",
        }
    }
    _extension = "midi"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)
