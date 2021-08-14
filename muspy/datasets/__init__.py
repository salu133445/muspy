"""Dataset classes.

This module provides an easy-to-use dataset management system. Each
supported dataset in MusPy comes with a class inherited from the base
MusPy Dataset class. It also provides interfaces to PyTorch and
TensorFlow for creating input pipelines for machine learning.

Base Classes
------------

- ABCFolderDataset
- Dataset
- DatasetInfo
- FolderDataset
- RemoteABCFolderDataset
- RemoteDataset
- RemoteFolderDataset
- RemoteMusicDataset
- MusicDataset

Dataset Classes
---------------
- EssenFolkSongDatabase
- EMOPIADataset
- HaydnOp20Dataset
- HymnalDataset
- HymnalTuneDataset
- JSBChoralesDataset
- LakhMIDIAlignedDataset
- LakhMIDIDataset
- LakhMIDIMatchedDataset
- MAESTRODatasetV1
- MAESTRODatasetV2
- Music21Dataset
- MusicNetDataset
- NESMusicDatabase
- NottinghamDatabase
- WikifoniaDataset

"""

from .base import (
    ABCFolderDataset,
    Dataset,
    DatasetInfo,
    FolderDataset,
    MusicDataset,
    RemoteABCFolderDataset,
    RemoteDataset,
    RemoteFolderDataset,
    RemoteMusicDataset,
)
from .emopia import EMOPIADataset
from .essen import EssenFolkSongDatabase
from .haydn import HaydnOp20Dataset
from .hymnal import HymnalDataset, HymnalTuneDataset
from .jsb import JSBChoralesDataset
from .lmd import (
    LakhMIDIAlignedDataset,
    LakhMIDIDataset,
    LakhMIDIMatchedDataset,
)
from .maestro import MAESTRODatasetV1, MAESTRODatasetV2, MAESTRODatasetV3
from .music21 import Music21Dataset
from .musicnet import MusicNetDataset
from .nes import NESMusicDatabase
from .nmd import NottinghamDatabase
from .wikifonia import WikifoniaDataset
from .wrapper import get_dataset, list_datasets

__all__ = [
    "ABCFolderDataset",
    "Dataset",
    "DatasetInfo",
    "EMOPIADataset",
    "EssenFolkSongDatabase",
    "FolderDataset",
    "HaydnOp20Dataset",
    "HymnalDataset",
    "HymnalTuneDataset",
    "JSBChoralesDataset",
    "LakhMIDIAlignedDataset",
    "LakhMIDIDataset",
    "LakhMIDIMatchedDataset",
    "MAESTRODatasetV1",
    "MAESTRODatasetV2",
    "MAESTRODatasetV3",
    "Music21Dataset",
    "MusicDataset",
    "MusicNetDataset",
    "NESMusicDatabase",
    "NottinghamDatabase",
    "RemoteABCFolderDataset",
    "RemoteDataset",
    "RemoteFolderDataset",
    "RemoteMusicDataset",
    "WikifoniaDataset",
    "get_dataset",
    "list_datasets",
]
