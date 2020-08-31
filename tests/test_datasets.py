"""Test cases for dataset module."""
import tempfile
from pathlib import Path

import muspy
from muspy import Music21Dataset, NottinghamDatabase


def test_music21_dataset():
    temp_dir = Path(tempfile.mkdtemp())

    dataset = Music21Dataset("demos")
    dataset.convert(temp_dir, ignore_exceptions=True)


def test_nmd_dataset():
    temp_dir = Path(tempfile.mkdtemp())

    dataset = NottinghamDatabase(temp_dir, download_and_extract=True)
    music = dataset[0]
