"""EMOPIA Dataset."""
from pathlib import Path
import pandas as pd
import os

from typing import (
    Optional,
    Union,
    List,
)

from ..inputs import read_midi
from ..music import Music
from ..classes import Annotation
from .base import DatasetInfo, RemoteFolderDataset

_NAME = "EMOPIA Dataset"
_DESCRIPTION = """\
EMOPIA (pronounced ‘yee-mò-pi-uh’) dataset is a shared multi-modal (audio and MIDI) \
database focusing on perceived emotion in pop piano music,\
to facilitate research on various tasks related to music emotion. \
The dataset contains 1,087 music clips from 387 songs \
and clip-level emotion labels annotated by four dedicated annotators. """
_HOMEPAGE = "https://annahung31.github.io/EMOPIA/"
_LICENSE = "Creative Commons Attribution 4.0 International License (CC-By 4.0)"
_CITATION = """\
@inproceedings{{EMOPIA},
         author = {Hung, Hsiao-Tzu and Ching, Joann and Doh, Seungheon and Kim, Nabin and Nam, Juhan and Yang, Yi-Hsuan},
         title = {{MOPIA}: A Multi-Modal Pop Piano Dataset For Emotion Recognition and Emotion-based Music Generation},
         booktitle = {Proc. Int. Society for Music Information Retrieval Conf.},
         year = {2021}}"""


class EMOPIADataset(RemoteFolderDataset):
    """EMOPIA Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _LICENSE)
    _citation = _CITATION
    _sources = {
        "emopia": {
            "filename": "EMOPIA_2.1.zip",
            "url": "https://zenodo.org/record/5151045/files/EMOPIA_2.1.zip",
            "archive": True,
            "md5": "c7ae6700a495f3203b271692c587927f",
            "sha256": "609309244444f88c0205e1381cc79d2bf7154f2a387a6f9f0229a54f92f89578",
        }
    }

    _extension = "mid"


    def read(self, filename: Union[str, Path]) -> Music:
        
        """Read a file into a Music object."""
        music = read_midi(self.root / filename)
        annotations = get_annotations(str(filename))
        music.annotations = annotations
        return music


def get_annotations(filename: str) -> List[Annotation]:
    """return the emotion class as an annotation object"""
    f = os.path.basename(os.path.normpath(filename))
    annotations = []
    annotation = {
            
            "emo_class": f[1],
            "YouTube_ID": f[3:14],
            "seg_id": f.split('_')[-1][:-4]
            
    }
    annotations.append(Annotation(time=0, annotation=annotation))
    

    return annotations
