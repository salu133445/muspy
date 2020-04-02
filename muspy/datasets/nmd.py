"""Nottingham Music Database."""
from .base import MusicDataset


class NottinghamMusicDatabase(MusicDataset):
    """Nottingham Music Database."""

    sources = {
        "nmd": {
            "filename": "NMD.zip",
            # TODO: this link seems no longer available?
            "url": "http://abc.sourceforge.net/NMD/nmd/NMD.zip",
            "md5": None,
        }
    }

    default_subsets = ["nmd"]
