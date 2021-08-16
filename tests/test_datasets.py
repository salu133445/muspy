"""Test cases for dataset module."""
import shutil

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

from .utils import (
    TEST_JSON_GZ_PATH,
    TEST_JSON_PATH,
    TEST_YAML_GZ_PATH,
    TEST_YAML_PATH,
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
    assert len(list_datasets()) == 17


def test_music_dataset(tmp_path):
    shutil.copyfile(TEST_JSON_GZ_PATH, tmp_path / TEST_JSON_GZ_PATH.name)
    shutil.copyfile(TEST_JSON_PATH, tmp_path / TEST_JSON_PATH.name)
    shutil.copyfile(TEST_YAML_GZ_PATH, tmp_path / TEST_YAML_GZ_PATH.name)
    shutil.copyfile(TEST_YAML_PATH, tmp_path / TEST_YAML_PATH.name)

    dataset = MusicDataset(tmp_path)
    assert len(dataset) == 4


def test_music21():
    dataset = Music21Dataset("demos")
    assert dataset[0] is not None


def test_convert(tmp_path):
    dataset = Music21Dataset("demos")
    dataset.convert(tmp_path)

    folder_dataset = MusicDataset(tmp_path)
    assert folder_dataset[0] is not None


def test_split(tmp_path):
    dataset = Music21Dataset("demos")
    dataset.split(filename=tmp_path / "splits.txt", splits=(0.8, 0.1, 0.1))


def test_to_pytorch_dataset():
    dataset = Music21Dataset("demos")
    pytorch_dataset = dataset.to_pytorch_dataset(representation="pitch")
    assert pytorch_dataset[0] is not None


def test_to_tensorflow_dataset():
    tf.config.set_visible_devices([], "GPU")
    dataset = Music21Dataset("demos")
    tensorflow_dataset = dataset.to_tensorflow_dataset(representation="pitch")
    assert tensorflow_dataset.take(1) is not None
