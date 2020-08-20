"""Test cases for score visualization."""
import muspy

from .utils import TEST_JSON_PATH

def test_show_score():
    music = muspy.load(TEST_JSON_PATH)
    music.show_score()
