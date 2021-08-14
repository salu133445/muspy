"""Nottingham Database."""
from .base import DatasetInfo, RemoteABCFolderDataset

# pylint: disable=line-too-long

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

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _sources = {
        "nmd": {
            "filename": "nottingham_database.zip",
            "url": "http://ifdo.ca/~seymour/nottingham/nottingham_database.zip",
            "archive": True,
            "size": 142934,
            "md5": "f55c354aaf08bcb6e9b2b3b8d52e4df3",
            "sha256": "f79a4bffe78b16d630d4d69f9c62775a7aa246d0973c4d8714ab6c5139ff5a3b",
        }
    }
