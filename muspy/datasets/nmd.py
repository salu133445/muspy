"""Nottingham Music Database."""
from .base import MusicDataset


class NottinghamMusicDatabase(MusicDataset):
    """Nottingham Music Database."""

    _sources = {
        "nmd": {
            "filename": "NMD.zip",
            # TODO: this link seems no longer available?
            "url": "http://abc.sourceforge.net/NMD/nmd/NMD.zip",
            "archive": True,
            "md5": None,
        }
    }

    _default_subsets = ["nmd"]
