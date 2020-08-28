"""Test cases for pypianoroll I/O."""

import muspy

from .utils import TEST_JSON_PATH, check_tempos, check_tracks


def test_to_pypianoroll():
    music = muspy.load(TEST_JSON_PATH)

    multitrack = muspy.to_pypianoroll(music)
    loaded = muspy.from_pypianoroll(multitrack)

    check_tempos(loaded.tempos)
    check_tracks(loaded.tracks, loaded.resolution)
