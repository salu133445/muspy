"""Test cases for score visualization."""
import muspy

from .utils import TEST_JSON_PATH


def test_show_score():
    muspy.download_bravura_font()
    music = muspy.load(TEST_JSON_PATH)
    music.show_score()
