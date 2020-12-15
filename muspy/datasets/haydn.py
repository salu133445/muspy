"""Haydn Op.20 Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import from_music21_score
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

import music21

_NAME = "Haydn Op.20 Dataset."
_DESCRIPTION = """\
This dataset is a set of functional harmonic analysis annotations \
for the Op.20 string quartets from Joseph Haydn, commonly known as \
the 'Sun' quartets."""
_HOMEPAGE = "https://doi.org/10.5281/zenodo.1095630"
_CITATION = """\
@dataset{nestor_napoles_lopez_2017_1095630, \
  author       = {N\'apoles L\'opez, N\'estor}, \
  title        = {{Joseph Haydn - String Quartets Op.20 - Harmonic \
                   Analysis Annotations Dataset}}, \
  month        = dec, \
  year         = 2017, \
  publisher    = {Zenodo}, \
  version      = {v1.1-alpha}, \
  doi          = {10.5281/zenodo.1095630}, \
  url          = {https://doi.org/10.5281/zenodo.1095630} \
}"""


class HaydnOp20Dataset(RemoteFolderDataset):
    """Haydn Op.20 Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _citation = _CITATION
    _sources = {
        "haydn": {
            "filename": "haydnop20v1.3_annotated.zip",
            "url": (
                "https://github.com/napulen/haydn_op20_harm/releases/download/v1.3/haydnop20v1.3_annotated.zip"
            ),
            "archive": True,
            "size": 130954,
            "md5": "1c65c8da312e1c9dda681d0496bf527f",
            "sha256": "96986cccebfd37a36cc97a2fc0ebcfbe22d5136e622b21e04ea125d589f5073b"
        }
    }
    _extension = "hrm"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        s = music21.converter.parse(filename, format='humdrum')
        # Getting the annotations
        rna = list(s.flat.getElementsByClass('RomanNumeral'))
        # Remove the annotations from the original score
        # (they mess with the python representation)
        s.remove(rna, recurse=True)
        music = from_music21_score(s)
        return music
