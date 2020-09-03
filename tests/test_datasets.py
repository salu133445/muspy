"""Test cases for dataset module."""
import tempfile
from pathlib import Path

import muspy
from muspy import Music21Dataset, NottinghamDatabase


def test_music21():
    dataset = Music21Dataset("demos")
    dataset[0]


def test_convert():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    dataset.convert(temp_dir)


def test_split():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    dataset.split(filename=temp_dir / "splits.txt", splits=(0.8, 0.1, 0.1))


def test_to_pytorch_dataset():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    pytorch_dataset = dataset.to_pytorch_dataset(representation="pitch")
    pytorch_dataset[0]


def test_to_tensorflow_dataset():
    dataset = Music21Dataset("demos")
    temp_dir = Path(tempfile.mkdtemp())
    tensorflow_dataset = dataset.to_tensorflow_dataset(representation="pitch")
    tensorflow_dataset.take(1)


def test_nmd():
    temp_dir = Path(tempfile.mkdtemp())

    dataset = NottinghamDatabase(temp_dir, download_and_extract=True)
    dataset[0]
