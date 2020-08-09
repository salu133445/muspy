"""Test cases for JSON/YAML I/O."""
import shutil
import tempfile
from pathlib import Path

import muspy

from .utils import TEST_JSON_PATH, TEST_YAML_PATH, check_music


def test_load_save_json():
    music = muspy.load(TEST_JSON_PATH)
    check_music(music)

    test_dir = Path(tempfile.mkdtemp())
    music.save(test_dir / "test.json")
    shutil.rmtree(test_dir)


def test_load_save_yaml():
    music = muspy.load(TEST_YAML_PATH)
    check_music(music)

    test_dir = Path(tempfile.mkdtemp())
    music.save(test_dir / "test.yaml")
    shutil.rmtree(test_dir)
