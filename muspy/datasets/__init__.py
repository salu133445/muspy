"""
Datasets
========

This module provides an easy-to-use dataset management system. Each
supported dataset in MusPy comes with a class inherited from the base
MusPy Dataset class. It also provides interfaces to PyTorch and
TensorFlow for creating input pipelines for machine learning.

"""

from .base import Dataset, DatasetInfo, RemoteDataset
from .datasets import (
    ABCFolderDataset,
    FolderDataset,
    MusicDataset,
    RemoteABCFolderDataset,
    RemoteFolderDataset,
    RemoteMusicDataset,
)
from .essen import EssenFolkSongDatabase
from .hymnal import HymnalDataset, HymnalTuneDataset
from .jsb import JSBChoralesDataset
from .lmd import LakhMIDIDataset
from .maestro import MAESTRODatasetV1, MAESTRODatasetV2
from .music21 import Music21Dataset
from .nes import NESMusicDatabase
from .nmd import NottinghamDatabase
from .wikifonia import WikifoniaDataset

__all__ = [
    "ABCFolderDataset",
    "Dataset",
    "DatasetInfo",
    "EssenFolkSongDatabase",
    "FolderDataset",
    "HymnalDataset",
    "HymnalTuneDataset",
    "JSBChoralesDataset",
    "LakhMIDIDataset",
    "MAESTRODatasetV1",
    "MAESTRODatasetV2",
    "Music21Dataset",
    "MusicDataset",
    "NESMusicDatabase",
    "NottinghamDatabase",
    "RemoteABCFolderDataset",
    "RemoteDataset",
    "RemoteFolderDataset",
    "RemoteMusicDataset",
    "WikifoniaDataset",
]
