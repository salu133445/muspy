"""Test cases for schema validations."""
import tempfile
from pathlib import Path

import muspy

from .utils import TEST_JSON_PATH


def test_write_audio():
    muspy.download_musescore_soundfont()
    temp_dir = Path(tempfile.mkdtemp())
    music = muspy.load(TEST_JSON_PATH)
    music.write(temp_dir / "test.wav")
