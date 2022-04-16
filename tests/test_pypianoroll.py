"""Test cases for pypianoroll I/O."""
import numpy as np

import muspy

from .utils import TEST_JSON_PATH, check_tempos, check_tracks


def test_to_pypianoroll():
    music = muspy.load(TEST_JSON_PATH)

    multitrack = muspy.to_object(music, "pypianoroll")

    assert len(multitrack) == 1
    assert np.all(multitrack.tempo == 72)
    assert np.all(np.nonzero(multitrack.downbeat)[0] == [0, 12, 48])
    assert multitrack[0].pianoroll.shape == (54, 128)

    loaded = muspy.from_object(multitrack)

    check_tempos(loaded.tempos)
    assert loaded.barlines[0].time == 0
    assert loaded.barlines[1].time == music.resolution // 2
    assert loaded.barlines[2].time == music.resolution * 2
    check_tracks(loaded.tracks, loaded.resolution)
