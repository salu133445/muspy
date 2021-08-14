"""Essen Folk Song Database."""
from .base import DatasetInfo, RemoteABCFolderDataset

# pylint: disable=line-too-long

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

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _sources = {
        "essen": {
            "filename": "esac.zip",
            "url": "https://ifdo.ca/~seymour/runabc/esac/esac.zip",
            "archive": True,
            "size": 1700981,
            "md5": "4636bd27b8ba4c57d2ef7db00d9eedc1",
            "sha256": "7957cf8f7a036dac9d807330548816967a13a4f598247e2a0f38aeccf04c7553",
        }
    }
