"""Test cases for JSON/YAML I/O."""
import shutil
import tempfile
from pathlib import Path

import muspy

DIR = Path(__file__).parent
TEST_JSON_PATH = DIR / "data" / "test.json"
TEST_YAML_PATH = DIR / "data" / "test.yaml"


def test_load_save_json():
    music = muspy.load(TEST_JSON_PATH)
    test_dir = Path(tempfile.mkdtemp())
    music.save(test_dir / "test.json")
    shutil.rmtree(test_dir)


def test_load_save_yaml():
    music = muspy.load(TEST_YAML_PATH)
    test_dir = Path(tempfile.mkdtemp())
    music.save(test_dir / "test.yaml")
    shutil.rmtree(test_dir)
