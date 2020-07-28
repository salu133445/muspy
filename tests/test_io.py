"""Test cases for MusPy I/O functionality."""
import shutil
import tempfile
from pathlib import Path

import muspy

DIR = Path(__file__).parent
TEST_JSON_PATH = DIR / "data" / "test.json"
TEST_YAML_PATH = DIR / "data" / "test.yaml"
TEST_MIDI_PATH = DIR / "data" / "midi" / "fur_elise.mid"
TEST_XML_PATH = DIR / "data" / "musicxml" / "fur_elise.xml"
TEST_MXL_PATH = DIR / "data" / "musicxml" / "fur_elise.mxl"


def test_load_save_json():
    test_dir = Path(tempfile.mkdtemp())
    music = muspy.load(TEST_JSON_PATH)
    music.save(test_dir / "test.json")
    shutil.rmtree(test_dir)


def test_load_save_yaml():
    test_dir = Path(tempfile.mkdtemp())
    music = muspy.load(TEST_YAML_PATH)
    music.save(test_dir / "test.yaml")
    shutil.rmtree(test_dir)
