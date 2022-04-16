"""Test cases for MusPy classes."""
from copy import deepcopy
from inspect import isclass
from operator import attrgetter

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
    assert music.get_real_end_time() == 1.875  # 2.25 / 72 * 60


def test_infer_barlines():
    music = muspy.load(TEST_JSON_PATH)
    music.infer_barlines(overwrite=True)

    assert len(music.barlines) == 2

    times = [0, 36]
    for barline, time in zip(music.barlines, times):
        assert barline.time == time


def test_infer_barlines_and_beats():
    music = muspy.load(TEST_JSON_PATH)
    music.infer_barlines_and_beats(overwrite=True)

    assert len(music.barlines) == 2
    assert len(music.beats) == 5

    times = [0, 36]
    for barline, time in zip(music.barlines, times):
        assert barline.time == time

    times = [0, 12, 24, 36, 48]
    for beat, time in zip(music.beats, times):
        assert beat.time == time


def test_adjust_resolution():
    music = muspy.load(TEST_JSON_PATH)
    music.adjust_resolution(12)
    check_tracks(music.tracks, resolution=12)


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


def test_trim():
    music = muspy.load(TEST_JSON_PATH)

    music.trim(24)
    assert len(music.beats) == 2
    assert len(music[0].notes) == 4
    assert music.get_end_time() == 24


def test_deepcopy():
    music = muspy.load(TEST_JSON_PATH)
    music2 = deepcopy(music)

    assert music2 == music
    assert music2 is not music
    assert music2.tracks is not music.tracks
    assert music2.tracks[0] is not music.tracks[0]
    assert music2.tracks[0][0] is not music.tracks[0][0]


def test_obj_extend():
    music = muspy.load(TEST_JSON_PATH)
    music2 = deepcopy(music).transpose(2)
    merged = deepcopy(music).extend(music2)

    for attr in music._list_attributes:
        g = attrgetter(attr)
        assert g(merged) == g(music) + g(music2)

        for a, b in zip(g(merged)[::-1], g(music2)[::-1]):
            assert a == b
            assert not isclass(a) or a is not b


def test_obj_extend_no_copy():
    music = muspy.load(TEST_JSON_PATH)
    music2 = deepcopy(music).transpose(2)
    music.extend(music2, deepcopy=False)

    for attr in music._list_attributes:
        g = attrgetter(attr)
        for a, b in zip(g(music)[::-1], g(music2)[::-1]):
            assert a is b
