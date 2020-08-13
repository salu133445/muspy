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
    check_metadata,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_empty():
    music = muspy.read(TEST_MIDI_DIR / "empty.mid")

    assert len(music.tracks) == 0
    assert music.metadata.source_format == "midi"


def test_type2():
    with pytest.raises(MIDIError):
        music = muspy.read(TEST_MIDI_DIR / "type2.mid")


def test_resolution():
    music = muspy.read(TEST_MIDI_DIR / "ticks-per-beat-480.mid")

    assert music.resolution == 480


def test_zero_ticks_per_beat():
    with pytest.raises(MIDIError):
        music = muspy.read(TEST_MIDI_DIR / "zero-ticks-per-beat.mid")


def test_negative_ticks_per_beat():
    with pytest.raises(MIDIError):
        music = muspy.read(TEST_MIDI_DIR / "negative-ticks-per-beat.mid")


def test_multiple_copyrights():
    music = muspy.read(TEST_MIDI_DIR / "multiple-copyrights.mid")

    assert (
        music.metadata.copyright == "Test copyright. Another test copyright."
    )


def test_pitches():
    music = muspy.read(TEST_MIDI_DIR / "pitches.mid")

    assert len(music.tracks) == 1

    notes = music.tracks[0].notes
    assert len(notes) == 128

    for i, note in enumerate(notes):
        assert note.start == music.resolution * i
        assert note.duration == music.resolution
        assert note.pitch == i


def test_durations():
    music = muspy.read(TEST_MIDI_DIR / "durations.mid")

    assert len(music.tracks) == 1

    notes = music.tracks[0].notes
    assert len(notes) == 11

    # Answers
    durations = [
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
    ]

    for note, duration in zip(notes, durations):
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
    numerators = [2, 4, 2, 3, 2, 3, 4, 5, 3, 6, 12]
    denominators = [2, 4, 2, 2, 4, 4, 4, 4, 8, 8, 8]
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
    keys = [
        "A",
        "A#m",
        "Ab",
        "Abm",
        "Am",
        "B",
        "Bb",
        "Bbm",
        "Bm",
        "C",
        "C#",
        "C#m",
        "Cb",
        "Cm",
        "D",
        "D#m",
        "Db",
        "Dm",
        "E",
        "Eb",
        "Ebm",
        "Em",
        "F",
        "F#",
        "F#m",
        "Fm",
        "G",
        "G#m",
        "Gb",
        "Gm",
    ]
    is_majors = ["m" not in key for key in keys]
    roots = [key.strip("m") for key in keys]

    for i, key_signature in enumerate(music.key_signatures):
        assert key_signature.time == 4 * music.resolution * i
        assert key_signature.root == roots[i]
        if is_majors[i]:
            assert key_signature.mode == "major"
        else:
            assert key_signature.mode == "minor"


def test_chords():
    music = muspy.read(TEST_MIDI_DIR / "chords.mid")

    notes = music.tracks[0].notes
    assert len(notes) == 12

    # Answers
    pitches = [60, 64, 67]

    for i, note in enumerate(notes):
        assert note.start == 2 * music.resolution * (i // 3)
        assert note.duration == music.resolution
        assert note.pitch == pitches[i % 3]


def test_single_track_multiple_channels():
    music = muspy.read(TEST_MIDI_DIR / "multichannel.mid")

    assert len(music.tracks) == 4

    # Answers
    pitches = [60, 64, 67, 72]

    for track, pitch in zip(music.tracks, pitches):
        assert track.notes[0].start == 0
        assert track.notes[0].duration == music.resolution
        assert track.notes[0].pitch == pitch


def test_multitrack():
    music = muspy.read(TEST_MIDI_DIR / "multitrack.mid")

    assert len(music.tracks) == 4

    # Answers
    pitches = [60, 64, 67, 72]

    for i, (track, pitch) in enumerate(zip(music.tracks, pitches)):
        assert track.name == "Track " + str(i)
        assert track.notes[0].start == 0
        assert track.notes[0].duration == 4 * music.resolution
        assert track.notes[0].pitch == pitch


def test_realworld():
    music = muspy.read(TEST_MIDI_DIR / "fur-elise.mid")

    assert music.metadata.source_filename == "fur-elise.mid"
    assert music.metadata.source_format == "midi"

    assert len(music.tracks) == 2

    assert len(music.tempos) == 2
    assert round(music.tempos[0].qpm) == 72
    assert round(music.tempos[1].qpm) == 72

    assert len(music.key_signatures) == 2
    assert music.key_signatures[0].root == "C"
    assert music.key_signatures[0].mode == "major"

    assert len(music.time_signatures), 7

    numerators = [1, 3, 2, 1, 3, 3, 2]
    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.numerator == numerators[i]
        assert time_signature.denominator == 8


def test_write():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.mid")

    loaded = muspy.read(temp_dir / "test.mid")

    assert loaded.resolution == 4
    assert loaded.metadata.title == "Für Elise"
    assert loaded.metadata.source_filename == "test.mid"
    assert loaded.metadata.source_format == "midi"

    check_tempos(music.tempos)
    check_key_signatures(music.key_signatures)
    check_time_signatures(music.time_signatures)
    check_lyrics(music.lyrics)
    check_tracks(music.tracks)
