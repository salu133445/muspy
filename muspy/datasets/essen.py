"""Essen Folk Song Database."""
from .base import RemoteABCFolderDataset

_NAME = "Essen Folk Song Database"
_DESCRIPTION = """\
This is a collection of about 8000 European and Chinese folk songs written in \
Essen Associative Code (EsAC). This database was started under the direction \
of the late Helmut Scaffrath who invented the EsAC code. Seymour Shlien \
converted the database into abc music notation using a tcl/tk script that \
Seymour Shlien wrote. Damien Sagrillo and Ewa Dahlig-Turek made available \
several other collections (HAYDN.SM, IRL.SM, LUX.SM, LOT.SM, HAN1.SM and \
HAN2.SM which were not publicly available.)"""
_HOMEPAGE = "https://ifdo.ca/~seymour/runabc/esac/esacdatabase.html"


class EssenFolkSongDatabase(RemoteABCFolderDataset):
    """Essen Folk Song Database."""

    _sources = {
        "essen": {
            "filename": "esac.zip",
            "url": "https://ifdo.ca/~seymour/runabc/esac/esac.zip",
            "archive": True,
            "size": 1700981,
            "md5": None,
        }
    }
