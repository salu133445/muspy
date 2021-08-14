"""Lakh MIDI Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "Lakh MIDI Dataset"
_DESCRIPTION = """\
The Lakh MIDI dataset is a collection of 176,581 unique MIDI files, 45,129 of \
which have been matched and aligned to entries in the Million Song Dataset. \
Its goal is to facilitate large-scale music information retrieval, both \
symbolic (using the MIDI files alone) and audio content-based (using \
information extracted from the MIDI files as annotations for the matched \
audio files)."""
_HOMEPAGE = "https://colinraffel.com/projects/lmd/"
_LICENSE = "Creative Commons Attribution 4.0 International License (CC-By 4.0)"
_CITATION = """\
@phdthesis{raffel2016learning,
  author={Colin Raffel},
  title={Learning-Based Methods for Comparing Sequences, with Applications to Audio-to-{MIDI} Alignment and Matching},
  year=2016
}"""


class LakhMIDIDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "lmd_full": {
            "filename": "lmd_full.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz",
            "archive": True,
            "size": 1768163879,
            "md5": "2536ce3fd2cede53ddaa264f731859ab",
            "sha256": "6fcfe2ac49ca08f3f214cec86ab138d4fc4dabcd7f27f491a838dae6db45a12b",
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)


class LakhMIDIMatchedDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset - matched subset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "lmd_matched": {
            "filename": "lmd_matched.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz",
            "archive": True,
            "size": 1407072670,
            "md5": "fb80d01c22020295bb3eeef31f1aa63a",
            "sha256": "621ff830aed771f469e5bfa13dc12a33c6ed69090adeda63d0b5c47783af0191",
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)


class LakhMIDIAlignedDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset - aligned subset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "lmd_aligned": {
            "filename": "lmd_aligned.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_aligned.tar.gz",
            "archive": True,
            "size": 272169548,
            "md5": "d36ca9159966d81d97e1e37d10ed4584",
            "sha256": "2bf5400e82eba73204644946515489b68811e1e656b0cfd854efc14377f6e53b",
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)
