"""Wrapper function."""
from typing import Type

from .base import Dataset
from .essen import EssenFolkSongDatabase
from .hymnal import HymnalDataset, HymnalTuneDataset
from .jsb import JSBChoralesDataset
from .lmd import (
    LakhMIDIAlignedDataset,
    LakhMIDIDataset,
    LakhMIDIMatchedDataset,
)
from .maestro import MAESTRODatasetV1, MAESTRODatasetV2
from .music21 import Music21Dataset
from .nes import NESMusicDatabase
from .nmd import NottinghamDatabase
from .wikifonia import WikifoniaDataset


def list_datasets():
    """Return all supported dataset classes as a list.

    Returns
    -------
    A list of all supported dataset classes.

    """
    return [
        EssenFolkSongDatabase,
        HymnalDataset,
        HymnalTuneDataset,
        JSBChoralesDataset,
        LakhMIDIAlignedDataset,
        LakhMIDIDataset,
        LakhMIDIMatchedDataset,
        MAESTRODatasetV1,
        MAESTRODatasetV2,
        Music21Dataset,
        NESMusicDatabase,
        NottinghamDatabase,
        WikifoniaDataset,
    ]


def get_dataset(key: str) -> Type[Dataset]:
    """Return a certain dataset class by key.

    Parameters
    ----------
    key : str
        Dataset key (case-insensitive).

    Returns
    -------
    The corresponding dataset class.

    """
    key = key.lower()
    if key == "essen":
        return EssenFolkSongDatabase
    if key.startswith("hymnal"):
        if key == "hymnal":
            return HymnalDataset
        if key == "hymnal-tune":
            return HymnalTuneDataset
    if key == "jsb":
        return JSBChoralesDataset
    if key.startswith("lmd"):
        if key in ("lmd", "lmd-full"):
            return LakhMIDIDataset
        if key == "lmd-matched":
            return LakhMIDIMatchedDataset
        if key == "lmd-aligned":
            return LakhMIDIAlignedDataset
    if key.startswith("maestro"):
        if key in ("maestro", "maestro-v2"):
            return MAESTRODatasetV2
        if key == "maestro-v1":
            return MAESTRODatasetV1
    if key == "music21":
        return Music21Dataset
    if key == "nes":
        return NESMusicDatabase
    if key == "nmd":
        return NottinghamDatabase
    if key == "wikifonia":
        return WikifoniaDataset
    raise ValueError("Unrecognized dataset key : {}.".format(key))
