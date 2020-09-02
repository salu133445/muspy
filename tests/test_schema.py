"""Test cases for schema validations."""
import muspy

from .utils import TEST_JSON_PATH, TEST_YAML_PATH, TEST_MUSICXML_LILYPOND_DIR


def test_yaml_schema():
    muspy.validate_yaml(TEST_YAML_PATH)


def test_json_schema():
    muspy.validate_json(TEST_JSON_PATH)


def test_musicxml_schema():
    muspy.validate_musicxml(
        TEST_MUSICXML_LILYPOND_DIR / "01a-Pitches-Pitches.xml"
    )
