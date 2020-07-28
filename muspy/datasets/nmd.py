"""Nottingham Database."""
from .datasets import RemoteABCFolderDataset

_NAME = "Nottingham Database"
_DESCRIPTION = """\
This is a collection of 1200 British and American folk tunes, (hornpipe, \
jigs, and etc.) that was created by Eric Foxley. The database was converted \
to ABC music notation format and was posted on http://abc.sourceforge.net/. \
The collection was edited by Seymour Shlien correcting missing beats during \
repeats and transitions."""
_HOMEPAGE = "https://ifdo.ca/~seymour/nottingham/nottingham.html"


class NottinghamDatabase(RemoteABCFolderDataset):
    """Nottingham Database."""

    _sources = {
        "nmd": {
            "filename": "nottingham_database.zip",
            "url": (
                "http://ifdo.ca/~seymour/nottingham/nottingham_database.zip"
            ),
            "archive": True,
            "size": 142934,
            "md5": None,
        }
    }
