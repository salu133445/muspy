"""Nottingham Music Database."""
from .base import Dataset


_NAME = "Nottingham Database"
_DESCRIPTION = """\
Nottingham Database is a collection of 1200 British and American folk tunes, \
(hornpipe, jigs, and etc.) that was created by Eric Foxley and posted on Eric Foxley's Music Database.
"""
_HOMEPAGE = "https://ifdo.ca/~seymour/nottingham/nottingham.html"
_CITATION = """
"""


class NottinghamMusicDatabase(Dataset):
    """Nottingham Music Database."""

    _sources = {
        "nmd": {
            "filename": "nottingham_database.zip",
            "url": "http://ifdo.ca/~seymour/nottingham/nottingham_database.zip",
            "archive": True,
            "md5": None,
        }
        # https://github.com/jukedeck/nottingham-dataset
    }
    _extension = "abc"

    @classmethod
    def _converter(cls, filename):
        pass
        """
        For Herman here
        """
        # if filename == "reelsH-L.abc":
            # return []
        # return read_midi(filename)
