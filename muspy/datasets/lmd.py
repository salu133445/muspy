"""Lakh MIDI Dataset."""
from .base import MusicDataset


class LakhMIDIDataset(MusicDataset):
    """Lakh MIDI Dataset."""

    _sources = {
        "lmd_full": {
            "filename": "lmd_full.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz",
            "archive": True,
            "md5": None,
        },
        "lmd_matched": {
            "filename": "lmd_matched.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz",
            "archive": True,
            "md5": None,
        },
        "lmd_aligned": {
            "filename": "lmd_aligned.tar.gz",
            "url": "http://hog.ee.columbia.edu/craffel/lmd/lmd_aligned.tar.gz",
            "archive": True,
            "md5": None,
        },
    }

    _default_subsets = ["lmd_full"]
