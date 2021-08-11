"""Test cases for dataset module."""
import tempfile
from pathlib import Path

import pytest
import tensorflow as tf

from muspy import (
    EMOPIADataset,
    EssenFolkSongDatabase,
    HaydnOp20Dataset,
    HymnalDataset,
    HymnalTuneDataset,
    JSBChoralesDataset,
    LakhMIDIAlignedDataset,
    LakhMIDIDataset,
    LakhMIDIMatchedDataset,
    MAESTRODatasetV1,
    MAESTRODatasetV2,
    MAESTRODatasetV3,
    Music21Dataset,
    MusicDataset,
    MusicNetDataset,
    NESMusicDatabase,
    NottinghamDatabase,
    WikifoniaDataset,
    get_dataset,
    list_datasets,
)


def test_get_dataset():
    answers = [
        ("essen", EssenFolkSongDatabase),
        ("emopia", EMOPIADataset),
        ("haydn", HaydnOp20Dataset),
        ("hymnal", HymnalDataset),
        ("hymnal-tune", HymnalTuneDataset),
        ("jsb", JSBChoralesDataset),
        ("lmd", LakhMIDIDataset),
        ("lmd-full", LakhMIDIDataset),
        ("lmd-matched", LakhMIDIMatchedDataset),
        ("lmd-aligned", LakhMIDIAlignedDataset),
        ("maestro", MAESTRODatasetV3),
        ("maestro-v1", MAESTRODatasetV1),
        ("maestro-v2", MAESTRODatasetV2),
        ("maestro-v3", MAESTRODatasetV3),
        ("music21", Music21Dataset),
        ("musicnet", MusicNetDataset),
        ("nes", NESMusicDatabase),
        ("nmd", NottinghamDatabase),
        ("wikifonia", WikifoniaDataset),
    ]
    for key, dataset in answers:
        assert get_dataset(key) == dataset

    with pytest.raises(ValueError):
        get_dataset("_")


def test_list_datasets():
    assert len(list_datasets()) == 16


def test_music21():
    dataset = Music21Dataset("demos")
    dataset[0]


def test_convert():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    dataset.convert(temp_dir)

    folder_dataset = MusicDataset(temp_dir)
    folder_dataset[0]


def test_split():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    dataset.split(filename=temp_dir / "splits.txt", splits=(0.8, 0.1, 0.1))


def test_to_pytorch_dataset():
    dataset = Music21Dataset("demos")
    pytorch_dataset = dataset.to_pytorch_dataset(representation="pitch")
    pytorch_dataset[0]


def test_to_tensorflow_dataset():
    tf.config.set_visible_devices([], "GPU")
    dataset = Music21Dataset("demos")
    tensorflow_dataset = dataset.to_tensorflow_dataset(representation="pitch")
    tensorflow_dataset.take(1)
