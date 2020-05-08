"""
Music Datasets
==============

This module provides classes for common datasets. All these datasets
inherit from the base class :class:`muspy.Dataset`.

"""

from .base import Dataset, DatasetInfo
from .datasets import FolderDataset, MusicDataset
from .hymnal import HymnalDataset, HymnalTuneDataset
from .jsb import JSBChoralesDataset
from .lmd import LakhMIDIDataset
from .maestro import MAESTRODatasetV1, MAESTRODatasetV2
from .music21 import Music21Dataset
from .nes import NESMusicDataset
from .nmd import NottinghamMusicDatabase
from .wikifornia import WikiforniaDataset

__all__ = [
    "Dataset",
    "DatasetInfo",
    "FolderDataset",
    "HymnalDataset",
    "HymnalTuneDataset",
    "JSBChoralesDataset",
    "LakhMIDIDataset",
    "MAESTRODatasetV1",
    "MAESTRODatasetV2",
    "Music21Dataset",
    "MusicDataset",
    "NESMusicDataset",
    "NottinghamMusicDatabase",
    "WikiforniaDataset",
]
