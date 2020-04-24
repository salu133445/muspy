"""
Music Datasets
==============

This module provides classes for common datasets. All these datasets
inherit from the base class :class:`muspy.Dataset`.

"""

from .base import Dataset
from .datasets import FolderDataset, MusicDataset
from .jsb import JSBChoralesDataset
from .lmd import LakhMIDIDataset
from .nmd import NottinghamMusicDatabase

__all__ = [
    "Dataset",
    "FolderDataset",
    "JSBChoralesDataset",
    "LakhMIDIDataset",
    "MusicDataset",
    "NottinghamMusicDatabase",
]
