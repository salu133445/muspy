"""Test cases for objective metrics."""
import math
from pathlib import Path

import muspy

TEST_JSON_PATH = Path(__file__).parent / "data" / "test.json"


def test_n_pitches_used():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.n_pitches_used(music) == 6


def test_n_chroma_used():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.n_chroma_used(music) == 6


def test_pitch_range():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.pitch_range(music) == 7


def test_empty_beat_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.empty_beat_rate(music) == 0


def test_empty_measure_rate():
    music = muspy.load(TEST_JSON_PATH)
    measure_resolution = int(1.5 * music.resolution)
    assert muspy.metrics.empty_measure_rate(music, measure_resolution) == 0


def test_polyphony():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.polyphony(music) == 1


def test_polyphony_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.polyphony_rate(music) == 0


def test_pitch_in_scale_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.pitch_in_scale_rate(music, 0, "major") == 7 / 9


def test_scale_consistency():
    music = muspy.load(TEST_JSON_PATH)
    assert muspy.metrics.scale_consistency(music) == 7 / 9


def test_drum_in_pattern_rate():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isnan(muspy.metrics.drum_in_pattern_rate(music, "duple"))


def test_drum_pattern_consistency():
    music = muspy.load(TEST_JSON_PATH)
    assert math.isnan(muspy.metrics.drum_pattern_consistency(music))


def test_groove_consistency():
    music = muspy.load(TEST_JSON_PATH)
    measure_resolution = int(1.5 * music.resolution)
    assert muspy.metrics.groove_consistency(music, measure_resolution) == 5 / 6
