"""Test cases for objective metrics."""
import math

import muspy
from muspy import (
    drum_in_pattern_rate,
    drum_pattern_consistency,
    empty_beat_rate,
    empty_measure_rate,
    groove_consistency,
    n_pitch_classes_used,
    n_pitches_used,
    pitch_class_entropy,
    pitch_entropy,
    pitch_in_scale_rate,
    pitch_range,
    polyphony,
    polyphony_rate,
    scale_consistency,
)

from .utils import TEST_JSON_PATH


def test_n_pitches_used():
    music = muspy.load(TEST_JSON_PATH)
    assert n_pitches_used(music) == 6


def test_n_pitch_classes_used():
    music = muspy.load(TEST_JSON_PATH)
    assert n_pitch_classes_used(music) == 6


def test_pitch_range():
    music = muspy.load(TEST_JSON_PATH)
    assert pitch_range(music) == 7


def test_empty_beat_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert empty_beat_rate(music) == 0


def test_empty_measure_rate():
    music = muspy.load(TEST_JSON_PATH)
    measure_resolution = int(1.5 * music.resolution)
    assert empty_measure_rate(music, measure_resolution) == 0


def test_polyphony():
    music = muspy.load(TEST_JSON_PATH)
    assert polyphony(music) == 1


def test_polyphony_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert polyphony_rate(music) == 0


def test_pitch_in_scale_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert pitch_in_scale_rate(music, 0, "major") == 7 / 9


def test_scale_consistency():
    music = muspy.load(TEST_JSON_PATH)
    assert scale_consistency(music) == 7 / 9


def test_drum_in_pattern_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isnan(drum_in_pattern_rate(music, "duple"))


def test_drum_pattern_consistency():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isnan(drum_pattern_consistency(music))


def test_groove_consistency():
    music = muspy.load(TEST_JSON_PATH)
    measure_resolution = int(1.5 * music.resolution)
    assert groove_consistency(music, measure_resolution) == 11 / 12


def test_pitch_entropy():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isclose(pitch_entropy(music), 2.4193819456463714)


def test_pitch_class_entropy():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isclose(pitch_class_entropy(music), 2.4193819456463714)
