"""JSB Chorales Dataset."""
from pathlib import Path
from typing import Union

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "JSB Chorales Dataset"
_DESCRIPTION = """\
The JSB Chorales Dataset is a collection of 382 four-part chorales by Johann \
Sebastian Bach. This dataset is used in the paper "Modeling Temporal \
Dependencies in High-Dimensional Sequences: Application to Polyphonic Music \
Generation and Transcription" in ICML 2012. It comes with train, test and \
validation split used in the paper "Harmonising Chorales by Probabilistic \
Inference" in NIPS 2005."""
_HOMEPAGE = "http://www-etud.iro.umontreal.ca/~boulanni/icml2012"
_CITATION = """\
@inproceedings{boulangerlewandowski2012modeling,
  author={Nicolas Boulanger-Lewandowski and Yoshua Bengio and Pascal \
Vincent},
  title={Modeling Temporal Dependencies in High-Dimensional Sequences: \
Application to Polyphonic Music Generation and Transcription},
  booktitle={Proceedings of the 29th International Conference on Machine \
Learning (ICML)},
  year={2012}
}"""


class JSBChoralesDataset(RemoteFolderDataset):
    """Johann Sebastian Bach Chorales Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "jsb": {
            "filename": "JSB Chorales.zip",
            "url": (
                "http://www-etud.iro.umontreal.ca/~boulanni/JSB%20Chorales.zip"
            ),
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mid"

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        music = read_midi(self.root / filename)

        # The resolution of MIDI file in this datset should be 120, but is
        # incorrectly set to 100
        music.timing.resolution = 120

        return music
