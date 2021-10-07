"""EMOPIA Dataset."""
from pathlib import Path
from typing import Union

from ..classes import Annotation
from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, RemoteFolderDataset

# pylint: disable=line-too-long

_NAME = "EMOPIA Dataset"
_DESCRIPTION = """\
EMOPIA (pronounced ‘yee-mò-pi-uh’) dataset is a shared multi-modal (audio and \
MIDI) database focusing on perceived emotion in pop piano music, to \
facilitate research on various tasks related to music emotion. The dataset \
contains 1,087 music clips from 387 songs and clip-level emotion labels \
annotated by four dedicated annotators."""
_HOMEPAGE = "https://annahung31.github.io/EMOPIA/"
_LICENSE = "Creative Commons Attribution 4.0 International License (CC-By 4.0)"
_CITATION = """\
@inproceedings{hung2021emopia,
  author={Hung, Hsiao-Tzu and Ching, Joann and Doh, Seungheon and Kim, Nabin and Nam, Juhan and Yang, Yi-Hsuan},
  title={{EMOPIA}: A Multi-Modal Pop Piano Dataset For Emotion Recognition and Emotion-based Music Generation},
  booktitle={Proceedings of the 22nd International Society for Music Information Retrieval Conference (ISMIR)},
  year=2021
}"""


class EMOPIADataset(RemoteFolderDataset):
    """EMOPIA Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "emopia": {
            "filename": "EMOPIA_2.2.zip",
            "url": "https://zenodo.org/record/5257995/files/EMOPIA_2.2.zip",
            "archive": True,
            "md5": "bad5171786a4898f37fc2678e99afd94",
        }
    }

    _extension = "mid"

    def get_raw_filenames(self):
        """Return a list of raw filenames."""
        return sorted(
            (
                filename
                for filename in self.root.rglob("*." + self._extension)
                if not str(filename.relative_to(self.root)).startswith(
                    "_converted/"
                )
                and not str(filename.relative_to(self.root)).startswith(
                    "__MACOSX/"
                )
            )
        )

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        music = read_midi(self.root / filename)
        music.annotations = [parse_annotation(Path(filename).name)]
        return music


def parse_annotation(filename: str) -> Annotation:
    """Parse the annotation from the filename."""
    annotation = {
        "emo_class": filename[1],
        "YouTube_ID": filename[3:14],
        "seg_id": filename.split("_")[-1][:-4],
    }
    return Annotation(time=0, annotation=annotation)
