"""Test cases for dataset module."""
import tempfile
from pathlib import Path

from muspy import Music21Dataset


def test_music21_dataset():
    temp_dir = Path(tempfile.mkdtemp())

    dataset = Music21Dataset("demos")
    dataset.convert(temp_dir, ignore_exceptions=True)
