"""Test cases for MIDI I/O."""
import tempfile
from pathlib import Path

import numpy as np
import pytest

import muspy
from muspy import MIDIError

from .utils import (
    TEST_JSON_PATH,
    TEST_MIDI_DIR,
    check_key_signatures,
    check_lyrics,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_empty():
    music = muspy.read(TEST_MIDI_DIR / "empty.mid")

    assert len(music) == 0
    assert music.metadata.source_format == "midi"


def test_type2():
    with pytest.raises(MIDIError):
        muspy.read(TEST_MIDI_DIR / "type2.mid")


def test_resolution():
    music = muspy.read(TEST_MIDI_DIR / "ticks-per-beat-480.mid")

    assert music.resolution == 480


def test_zero_ticks_per_beat():
    with pytest.raises(MIDIError):
        muspy.read(TEST_MIDI_DIR / "zero-ticks-per-beat.mid")


def test_negative_ticks_per_beat():
    with pytest.raises(MIDIError):
        muspy.read(TEST_MIDI_DIR / "negative-ticks-per-beat.mid")


def test_multiple_copyrights():
    music = muspy.read(TEST_MIDI_DIR / "multiple-copyrights.mid")

    assert (
        music.metadata.copyright == "Test copyright. Another test copyright."
    )


def test_pitches():
    music = muspy.read(TEST_MIDI_DIR / "pitches.mid")

    assert len(music) == 1

    assert len(music[0].notes) == 128
    for i, note in enumerate(music[0].notes):
        assert note.start == music.resolution * i
        assert note.duration == music.resolution
        assert note.pitch == i


def test_durations():
    music = muspy.read(TEST_MIDI_DIR / "durations.mid")

    assert len(music) == 1

    assert len(music[0].notes) == 11

    # Answers
    durations = (
        16,
        8,
        4,
        2,
        1,
        0.5,
        0.25,
        0.125,
        0.0625,
        0.03125,
        0.03125,
    )

    for note, duration in zip(music[0].notes, durations):
        assert note.duration == music.resolution * duration


def test_tempos():
    music = muspy.read(TEST_MIDI_DIR / "tempos.mid")

    assert len(music.tempos) == 2

    assert music.tempos[0].time == 0
    assert music.tempos[0].qpm == 100

    assert music.tempos[1].time == 4 * music.resolution
    assert music.tempos[1].qpm == 120


def test_time_signatures():
    music = muspy.read(TEST_MIDI_DIR / "time-signatures.mid")

    assert len(music.time_signatures) == 11

    # Answers
    numerators = (2, 4, 2, 3, 2, 3, 4, 5, 3, 6, 12)
    denominators = (2, 4, 2, 2, 4, 4, 4, 4, 8, 8, 8)
    starts = np.insert(
        np.cumsum(4 * np.array(numerators) / np.array(denominators)), 0, 0
    )

    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.time == int(music.resolution * starts[i])

        assert time_signature.numerator == numerators[i]
        assert time_signature.denominator == denominators[i]


def test_key_signatures():
    music = muspy.read(TEST_MIDI_DIR / "key-signatures.mid")

    # Answers
    is_majors = (
        True,
        False,
        True,
        False,
        False,
        True,
        True,
        False,
        False,
        True,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        True,
        False,
        False,
        True,
        True,
        False,
        False,
        True,
        False,
        True,
        False,
    )
    roots = (
        9,
        10,
        8,
        8,
        9,
        11,
        10,
        10,
        11,
        0,
        1,
        1,
        11,
        0,
        2,
        3,
        1,
        2,
        4,
        3,
        3,
        4,
        5,
        6,
        6,
        5,
        7,
        8,
        6,
        7,
    )

    for i, key_signature in enumerate(music.key_signatures):
        assert key_signature.time == 4 * music.resolution * i
        assert key_signature.root == roots[i]
        if is_majors[i]:
            assert key_signature.mode == "major"
        else:
            assert key_signature.mode == "minor"


def test_chords():
    music = muspy.read(TEST_MIDI_DIR / "chords.mid")

    assert len(music[0].notes) == 12

    # Answers
    pitches = [60, 64, 67]

    for i, note in enumerate(music[0].notes):
        assert note.start == 2 * music.resolution * (i // 3)
        assert note.duration == music.resolution
        assert note.pitch == pitches[i % 3]


def test_single_track_multiple_channels():
    music = muspy.read(TEST_MIDI_DIR / "multichannel.mid")

    assert len(music) == 4

    # Answers
    pitches = [60, 64, 67, 72]

    for track, pitch in zip(music.tracks, pitches):
        assert track.notes[0].start == 0
        assert track.notes[0].duration == music.resolution
        assert track.notes[0].pitch == pitch


def test_multitrack():
    music = muspy.read(TEST_MIDI_DIR / "multitrack.mid")

    assert len(music) == 4

    # Answers
    pitches = (60, 64, 67, 72)

    for i, (track, pitch) in enumerate(zip(music.tracks, pitches)):
        # TODO: Bad input file
        # assert track.name == "Track " + str(i)
        assert track.notes[0].start == 0
        assert track.notes[0].duration == 4 * music.resolution
        assert track.notes[0].pitch == pitch


def test_realworld():
    music = muspy.read(TEST_MIDI_DIR / "fur-elise.mid")

    assert music.metadata.source_filename == "fur-elise.mid"
    assert music.metadata.source_format == "midi"

    assert len(music) == 2

    assert len(music.tempos) == 2
    assert round(music.tempos[0].qpm) == 72
    assert round(music.tempos[1].qpm) == 72

    assert len(music.key_signatures) == 2
    assert music.key_signatures[0].root == 0
    assert music.key_signatures[0].mode == "major"

    assert len(music.time_signatures), 7

    numerators = (1, 3, 2, 1, 3, 3, 2)
    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.numerator == numerators[i]
        assert time_signature.denominator == 8


def test_write():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.mid")

    loaded = muspy.read(temp_dir / "test.mid")

    assert loaded.resolution == 24
    assert loaded.metadata.title == "Für Elise"
    assert loaded.metadata.source_filename == "test.mid"
    assert loaded.metadata.source_format == "midi"

    check_tempos(loaded.tempos, strict=False)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_lyrics(loaded.lyrics)
    check_tracks(loaded.tracks)


def test_read_pretty_midi_backend():
    music = muspy.read(TEST_MIDI_DIR / "fur-elise.mid", backend="pretty_midi")

    assert music.metadata.source_filename == "fur-elise.mid"
    assert music.metadata.source_format == "midi"

    assert len(music) == 2

    # pretty_midi removes duplicate tempos at time 0
    assert len(music.tempos) == 1
    assert round(music.tempos[0].qpm) == 72

    # pretty_midi removes duplicate key signatures at time 0
    assert len(music.key_signatures) == 1
    assert music.key_signatures[0].root == 0
    assert music.key_signatures[0].mode == "major"

    assert len(music.time_signatures), 7

    numerators = (1, 3, 2, 1, 3, 3, 2)
    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.numerator == numerators[i]
        assert time_signature.denominator == 8


def test_write_pretty_midi_backend():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.mid", backend="pretty_midi")

    loaded = muspy.read(temp_dir / "test.mid", backend="pretty_midi")

    assert loaded.resolution == 24
    assert loaded.metadata.source_filename == "test.mid"
    assert loaded.metadata.source_format == "midi"

    assert len(loaded.key_signatures) == 1
    assert len(loaded.time_signatures) == 1
    assert len(loaded.lyrics) == 1

    assert len(loaded) == 1
    assert len(loaded[0].notes) == 9
    assert loaded[0].program == 0
    assert not loaded[0].is_drum
    assert loaded[0].name == "Melody"
