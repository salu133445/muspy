"""NES Music Database."""
from pathlib import Path
from typing import Union

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "NES Music Database"
_DESCRIPTION = """\
The Nintendo Entertainment System Music Database (NES-MDB) is a dataset \
intended for building automatic music composition systems for the NES audio \
synthesizer. The NES synthesizer has highly constrained compositional \
parameters which are well-suited to a wide variety of current machine \
learning techniques. The synthesizer is typically programmed in assembly, but \
we parse the assembly into straightforward formats that are more suitable for \
machine learning."""
_HOMEPAGE = "https://github.com/chrisdonahue/nesmdb"
_CITATION = """\
@inproceedings{donahue2018nesmdb,
  author={Chris Donahue and Huanru Henry Mao and Julian McAuley},
  title={The {NES} Music Database: A multi-instrumental dataset with expressive performance attributes},
  booktitle={Proceedings of the 19th International Society for Music Retrieval Conference (ISMIR)},
  year=2018
}"""


class NESMusicDatabase(RemoteFolderDataset):
    """NES Music Database."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _citation = _CITATION
    _sources = {
        "nes": {
            "filename": "nesmdb_midi.tar.gz",
            "url": "http://deepyeti.ucsd.edu/cdonahue/nesmdb/nesmdb_midi.tar.gz",
            "archive": True,
            "size": 12922275,
            "md5": "3f3e8ab4f660dd1b19350e5a8a91f3e6",
            "sha256": "37610e2ca5fe70359c85170cf1f4982596783bb304c59d9c439f68c24ff4ee93",
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)
