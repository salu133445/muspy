"""Test cases for MusPy classes."""
import muspy

from .utils import TEST_JSON_PATH, check_tracks


def test_validate_type():
    music = muspy.load(TEST_JSON_PATH)
    music.validate_type()


def test_is_valid_type():
    music = muspy.load(TEST_JSON_PATH)
    assert music.is_valid_type()


def test_validate():
    music = muspy.load(TEST_JSON_PATH)
    music.validate()


def test_is_valid():
    music = muspy.load(TEST_JSON_PATH)
    assert music.is_valid()


def test_get_real_end_time():
    music = muspy.load(TEST_JSON_PATH)
    assert music.get_real_end_time() == 3.75


def test_adjust_resolution():
    music = muspy.load(TEST_JSON_PATH)
    music.adjust_resolution(2)
    check_tracks(music.tracks, resolution=2)


def test_clip():
    music = muspy.load(TEST_JSON_PATH)

    music.clip(lower=100)
    for note in music[0]:
        assert note.velocity == 100

    music.clip(upper=50)
    for note in music[0]:
        assert note.velocity == 50


def test_transpose():
    music = muspy.load(TEST_JSON_PATH)

    music.transpose(1)
    pitches = (76, 75, 76, 75, 76, 71, 74, 72, 69)
    for note, pitch in zip(music[0].notes, pitches):
        assert note.pitch == pitch + 1

    music.transpose(-1)
    for note, pitch in zip(music[0].notes, pitches):
        assert note.pitch == pitch
