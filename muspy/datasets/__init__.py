"""
Music Datasets
==============

This module provides classes for common datasets. All these datasets
inherit from the base class :class:`muspy.MusicDataset`.

"""

from .base import MusicDataset
from .jsb import JSBChoralesDataset
from .lmd import LakhMIDIDataset
from .nmd import NottinghamMusicDatabase

__all__ = [
    "JSBChoralesDataset",
    "LakhMIDIDataset",
    "MusicDataset",
    "NottinghamMusicDatabase",
]
