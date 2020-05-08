"""NES Music Database."""
from ..inputs import read_midi
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "NES Music Database"
_DESCRIPTION = """\
The Nintendo Entertainment System Music Database (NES-MDB) is a dataset \
intended for building automatic music composition systems for the NES audio \
synthesizer. The NES synthesizer has highly constrained compositional \
parameters which are well-suited to a wide variety of current machine \
learning techniques. The synthesizer is typically programmed in assembly, but \
we parse the assembly into straightforward formats that are more suitable for \
machine learning.
"""
_HOMEPAGE = "https://github.com/chrisdonahue/nesmdb"
_CITATION = """\
@inproceedings{donahue2018nesmdb,
  title={The {NES} Music Database: A multi-instrumental dataset with \
expressive performance attributes},
  author={Chris Donahue and Huanru Henry Mao and Julian McAuley},
  booktitle={Proceedings of the 19th International Society for Music \
Information Retrieval Conference (ISMIR)},
  year={2018}
}
"""


class NESMusicDataset(RemoteFolderDataset):
    """NES Music Database."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "lmd_full": {
            "filename": "nesmdb_midi.tar.gz",
            "url": (
                "http://deepyeti.ucsd.edu/cdonahue/nesmdb/nesmdb_midi.tar.gz"
            ),
            "archive": True,
            "sha256": (
                "37610e2ca5fe70359c85170cf1f4982596783bb304c59d9c439f68c24ff4e"
                "e93"
            ),
        }
    }
    _extension = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)
