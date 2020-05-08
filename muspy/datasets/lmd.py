"""Lakh MIDI Dataset."""
from ..inputs import read_midi
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "Lakh MIDI Dataset"
_DESCRIPTION = """\
The Lakh MIDI dataset is a collection of 176,581 unique MIDI files, 45,129 of \
which have been matched and aligned to entries in the Million Song Dataset. \
Its goal is to facilitate large-scale music information retrieval, both \
symbolic (using the MIDI files alone) and audio content-based (using \
information extracted from the MIDI files as annotations for the matched \
audio files).
"""
_HOMEPAGE = "https://colinraffel.com/projects/lmd/"
_CITATION = """\
@phdthesis{raffel2016learning
  title={Learning-Based Methods for Comparing Sequences, with Applications\
to Audio-to-{MIDI} Alignment and Matching},
  author={Colin Raffel},
  year={2016}
}
"""


class LakhMIDIDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "lmd_full": {
            "filename": "lmd_full.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz",
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)


class LakhMIDIMatchedDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset - matched subset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "lmd_matched": {
            "filename": "lmd_matched.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz",
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)


class LakhMIDIAlignedDataset(RemoteFolderDataset):
    """Lakh MIDI Dataset - aligned subset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "lmd_aligned": {
            "filename": "lmd_aligned.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_aligned.tar.gz",
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)
