"""Nottingham Music Database."""
from .base import Dataset


class NottinghamMusicDatabase(Dataset):
    """Nottingham Music Database."""

    _sources = {
        "nmd": {
            "filename": "NMD.zip",
            # TODO: this link seems no longer available?
            "url": "http://abc.sourceforge.net/NMD/nmd/NMD.zip",
            "archive": True,
            "md5": None,
        }
        # https://github.com/jukedeck/nottingham-dataset
    }
    _default_subsets = ["nmd"]
