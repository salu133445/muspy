"""Test cases for JSON/YAML I/O."""
import muspy

from .utils import (
    TEST_JSON_GZ_PATH,
    TEST_JSON_PATH,
    TEST_YAML_GZ_PATH,
    TEST_YAML_PATH,
    check_music,
)


def test_load_json_path():
    music = muspy.load(TEST_JSON_PATH)
    check_music(music)


def test_load_json_path_compressed():
    music = muspy.load(TEST_JSON_GZ_PATH)
    check_music(music)


def test_load_file():
    with open(TEST_JSON_PATH, encoding="utf-8") as f:
        music = muspy.load_json(f)
    check_music(music)


def test_load_yaml_path():
    music = muspy.load(TEST_YAML_PATH)
    check_music(music)


def test_load_yaml_path_compressed():
    music = muspy.load(TEST_YAML_GZ_PATH)
    check_music(music)


def test_load_yaml_file():
    with open(TEST_YAML_PATH, encoding="utf-8") as f:
        music = muspy.load_yaml(f)
    check_music(music)


def test_save_json_path(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    music.save(tmp_path / "test.json")

    loaded = muspy.load(tmp_path / "test.json")
    check_music(loaded)


def test_save_json_path_compressed(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    music.save(tmp_path / "test.json.gz")

    loaded = muspy.load(tmp_path / "test.json.gz")
    check_music(loaded)


def test_save_json_file(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    with open(tmp_path / "test.json", "w", encoding="utf-8") as f:
        music.save_json(f)

    loaded = muspy.load(tmp_path / "test.json")
    check_music(loaded)


def test_save_yaml_path(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    music.save(tmp_path / "test.yaml")

    loaded = muspy.load(tmp_path / "test.yaml")
    check_music(loaded)


def test_save_yaml_path_compressed(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    music.save(tmp_path / "test.yaml.gz")

    loaded = muspy.load(tmp_path / "test.yaml.gz")
    check_music(loaded)


def test_save_yaml_file(tmp_path):
    music = muspy.load(TEST_JSON_PATH)
    with open(tmp_path / "test.yaml", "w", encoding="utf-8") as f:
        music.save_yaml(f)

    loaded = muspy.load(tmp_path / "test.yaml")
    check_music(loaded)
