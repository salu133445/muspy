"""Haydn Op.20 Dataset."""
from pathlib import Path
from typing import List, Union

import music21
from music21.roman import RomanNumeral

from ..classes import Annotation
from ..inputs import from_music21_score
from ..music import DEFAULT_RESOLUTION, Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "Haydn Op.20 Dataset"
_DESCRIPTION = """\
This dataset is a set of functional harmonic analysis annotations \
for the Op.20 string quartets from Joseph Haydn, commonly known as \
the 'Sun' quartets."""
_HOMEPAGE = "https://doi.org/10.5281/zenodo.1095630"
_CITATION = """\
@dataset{nestor_napoles_lopez_2017_1095630,
  author={N\'apoles L\'opez, N\'estor},
  title={{Joseph Haydn - String Quartets Op.20 - Harmonic Analysis Annotations Dataset}},
  month=dec,
  year=2017,
  publisher={Zenodo},
  version={v1.1-alpha},
  doi={10.5281/zenodo.1095630},
  url={https://doi.org/10.5281/zenodo.1095630}
}"""


class HaydnOp20Dataset(RemoteFolderDataset):
    """Haydn Op.20 Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _citation = _CITATION
    _sources = {
        "haydn": {
            "filename": "haydnop20v1.3_annotated.zip",
            "url": "https://github.com/napulen/haydn_op20_harm/releases/download/v1.3/haydnop20v1.3_annotated.zip",
            "archive": True,
            "size": 130954,
            "md5": "1c65c8da312e1c9dda681d0496bf527f",
            "sha256": "96986cccebfd37a36cc97a2fc0ebcfbe22d5136e622b21e04ea125d589f5073b",
        }
    }
    _extension = "hrm"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        score = music21.converter.parse(filename, format="humdrum")

        # Get the annotations
        roman_numerals = list(score.flat.getElementsByClass("RomanNumeral"))
        annotations = get_annotations(roman_numerals)

        # Remove the annotations from the original score
        # (they mess with the python representation)
        score.remove(roman_numerals, recurse=True)

        music = from_music21_score(score)
        music.annotations = annotations

        return music


def get_annotations(
    roman_numerals: List[RomanNumeral], resolution=DEFAULT_RESOLUTION
) -> List[Annotation]:
    """Return music21 RomanNumeral objects as Annotation objects."""
    # Convert the list into a dictionary to remove duplicate items
    roman_numeral_dict = {rn.offset: rn for rn in roman_numerals if rn}

    annotations = []
    for offset, roman_numeral in roman_numeral_dict.items():
        time = int(round(float(offset * resolution)))
        tonicized_key = roman_numeral.secondaryRomanNumeralKey
        key = tonicized_key if tonicized_key else roman_numeral.key

        annotation = {
            "key": key.tonicPitchNameWithCase,
            "figure": roman_numeral.figure,
            "chord": roman_numeral.pitchedCommonName,
        }
        annotations.append(Annotation(time=time, annotation=annotation))

    return annotations
