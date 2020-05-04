"""
Music Datasets
==============

This module provides classes for common datasets. All these datasets
inherit from the base class :class:`muspy.Dataset`.

"""

from .base import Dataset, DatasetInfo
from .datasets import FolderDataset, MusicDataset
from .jsb import JSBChoralesDataset
from .lmd import LakhMIDIDataset
from .nmd import NottinghamMusicDatabase
from .wikifornia import WikiforniaDataset

__all__ = [
    "Dataset",
    "DatasetInfo",
    "FolderDataset",
    "JSBChoralesDataset",
    "LakhMIDIDataset",
    "MusicDataset",
    "NottinghamMusicDatabase",
    "WikiforniaDataset",
]
