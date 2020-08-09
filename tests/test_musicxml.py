"""Test cases for MusicXML I/O."""
import tempfile
from pathlib import Path

import numpy as np

import muspy

from .utils import (
    TEST_JSON_PATH,
    TEST_MUSICXML_DIR,
    TEST_MUSICXML_LILYPOND_DIR,
    check_key_signatures,
    check_lyrics,
    check_metadata,
    check_music,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_pitches():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "01a-Pitches-Pitches.xml")

    assert len(music.tracks) == 1

    notes = music.tracks[0].notes
    assert len(notes) == 102

    # Answers
    pitches = [43, 45, 47, 48]
    for octave in range(4):
        for pitch in [50, 52, 53, 55, 57, 59, 60]:
            pitches.append(12 * octave + pitch)

    # Without accidentals
    for i, note in enumerate(notes[:32]):
        assert note.pitch == pitches[i]

    # With a sharp
    for i, note in enumerate(notes[32:64]):
        assert note.pitch == pitches[i] + 1

    # With a flat
    for i, note in enumerate(notes[64:96]):
        assert note.pitch == pitches[i] - 1

    # Double alterations
    assert notes[96].pitch == 74
    assert notes[97].pitch == 70
    for note in notes[98:]:
        assert note.pitch == 73


def test_durations():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "03a-Rhythm-Durations.xml")

    assert music.resolution == 64
    assert len(music.tracks) == 1

    notes = music.tracks[0].notes
    assert len(notes) == 32

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
    durations_double_dotted = [
        16,
        8,
        4,
        2,
        1,
        0.5,
        0.25,
        0.125,
        0.0625,
        0.0625,
    ]

    # Without dots
    for i, note in enumerate(notes[:11]):
        assert note.duration == 64 * durations[i]

    # With a dot
    for i, note in enumerate(notes[11:22]):
        assert note.duration == 64 * durations[i] * 1.5

    # With double dots
    for i, note in enumerate(notes[22:]):
        assert note.duration == 64 * durations_double_dotted[i] * 1.75


def test_divisions():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "03c-Rhythm-DivisionChange.xml"
    )

    assert music.resolution == 152

    notes = music.tracks[0].notes
    assert len(notes) == 6

    assert notes[0].duration == music.resolution
    assert notes[4].duration == 2 * music.resolution


def test_time_signatures():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "11a-TimeSignatures.xml")

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


def test_compound_time_signatures():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "11c-TimeSignatures-CompoundSimple.xml"
    )

    assert len(music.time_signatures) == 2

    assert music.time_signatures[0].numerator == 5
    assert music.time_signatures[0].denominator == 8

    assert music.time_signatures[1].numerator == 9
    assert music.time_signatures[1].denominator == 4


def test_key_signatures():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "13a-KeySignatures.xml")

    assert len(music.key_signatures) == 46

    # Answers
    major_keys = [
        "Abb",
        "Ebb",
        "Bbb",
        "Fb",
        "Cb",
        "Gb",
        "Db",
        "Ab",
        "Eb",
        "Bb",
        "F",
        "C",
        "G",
        "D",
        "A",
        "E",
        "B",
        "F#",
        "C#",
        "G#",
        "D#",
        "A#",
        "E#",
    ]
    minor_keys = [
        "Fb",
        "Cb",
        "Gb",
        "Db",
        "Ab",
        "Eb",
        "Bb",
        "F",
        "C",
        "G",
        "D",
        "A",
        "E",
        "B",
        "F#",
        "C#",
        "G#",
        "D#",
        "A#",
        "E#",
        "B#",
        "F##",
        "C##",
    ]

    for i, key_signature in enumerate(music.key_signatures):
        if i % 2 == 0:
            assert key_signature.mode == "major"
            assert key_signature.root == major_keys[i // 2]
        else:
            assert key_signature.mode == "minor"
            assert key_signature.root == minor_keys[i // 2]


def test_church_modes():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "13b-KeySignatures-ChurchModes.xml"
    )

    # Answers
    modes = [
        "major",
        "minor",
        "ionian",
        "dorian",
        "phrygian",
        "lydian",
        "mixolydian",
        "aeolian",
        "locrian",
    ]

    for key_signature, answer in zip(music.key_signatures, modes):
        assert key_signature.mode == answer


def test_chords():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "21a-Chord-Basic.xml")

    notes = music.tracks[0].notes
    assert len(notes) == 2

    assert notes[0].start == 0
    assert notes[0].duration == music.resolution
    assert notes[0].pitch == 65

    assert notes[1].start == 0
    assert notes[1].duration == music.resolution
    assert notes[1].pitch == 69


def test_chords_and_durations():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "21c-Chords-ThreeNotesDuration.xml"
    )

    # Answers
    pitches = (
        [65, 69, 72]
        + [69, 79]
        + [65, 69, 72]
        + [65, 69, 72]
        + [65, 69, 76]
        + [65, 69, 77]
        + [65, 69, 74,]
    )
    durations = [1.5, 1.5, 1.5] + [0.5, 0.5] + [1, 1, 1] * 4 + [2, 2, 2]

    for i, note in enumerate(music.tracks[0].notes):
        assert note.duration == music.resolution * durations[i]
        assert note.pitch == pitches[i]


def test_pickup_measures():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "21e-Chords-PickupMeasures.xml"
    )

    # Answers
    pitches = [72, 65, 69, 72, 69, 72]
    starts = [0, 1, 1, 1, 2, 2]
    durations = [1, 1, 1, 1, 1, 1]

    for i, note in enumerate(music.tracks[0].notes):

        assert note.start == music.resolution * starts[i]
        assert note.duration == music.resolution * durations[i]
        assert note.pitch == pitches[i]


def test_tuplets():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "23a-Tuplets.xml")

    # Answers
    pitches = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84]
    pitches += pitches[::-1]
    durations = [2 / 3] * 9
    durations += [2 / 4] * 4
    durations += [1 / 4] * 4
    durations += [3 / 7] * 7
    durations += [2 / 6] * 6

    for i, note in enumerate(music.tracks[0].notes):
        assert note.pitch == pitches[i]
        assert note.duration == round(music.resolution * durations[i])


def test_grace_notes():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "24a-GraceNotes.xml")

    assert len(music.tracks[0].notes) == 13


def test_directions():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "31a-Directions.xml")

    assert len(music.tempos) == 1
    assert music.tempos[0].time == 11 * 4 * music.resolution
    assert music.tempos[0].tempo == 60


def test_metronome():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "31c-MetronomeMarks.xml")

    assert len(music.tempos) == 3

    # Answers
    qpms = [150, 1600, 115.5]

    for tempo, qpm in zip(music.tempos, qpms):
        assert tempo.tempo == qpm


def test_ties():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "33b-Spanners-Tie.xml")

    notes = music.tracks[0].notes
    assert len(notes) == 1

    assert notes[0].duration == music.resolution * 8
    assert notes[0].pitch == 65


def test_ties_not_ended():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "33i-Ties-NotEnded.xml")

    notes = music.tracks[0].notes
    assert len(notes) == 2

    assert notes[0].duration == music.resolution * 8
    assert notes[0].pitch == 72

    assert notes[1].duration == music.resolution * 12
    assert notes[1].pitch == 72


def test_parts():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "41a-MultiParts-Partorder.xml"
    )

    assert len(music.tracks) == 4

    # Answers
    pitches = [60, 64, 67, 71]

    for i, track in enumerate(music.tracks):
        assert track.name == "Part " + str(i + 1)
        assert track.notes[0].start == 0
        assert track.notes[0].duration == music.resolution
        assert track.notes[0].pitch == pitches[i]


def test_part_names_with_line_breaks():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR
        / "41e-StaffGroups-InstrumentNames-Linebroken.xml"
    )

    assert music.tracks[0].name == "Long Staff Name"


def test_part_without_id():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "41g-PartNoId.xml")

    assert music.resolution == 1
    assert len(music.tracks) == 1


def test_unlisted_parts():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "41h-TooManyParts.xml")

    assert len(music.tracks) == 1


def test_voices():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR
        / "42a-MultiVoice-TwoVoicesOnStaff-Lyrics.xml"
    )

    assert len(music.tracks) == 1

    # Answers
    pitches = [72, 76, 71, 74, 67, 71, 71, 74, 55, 59, 69, 72]
    starts = [0, 0, 2, 2, 3, 3, 5, 5, 6, 6, 7.5, 7.5]
    durations = [2, 2, 1, 1, 1, 1, 1, 1, 1.5, 1.5, 0.5, 0.5]

    for i, note in enumerate(music.tracks[0].notes):
        assert note.start == music.resolution * starts[i]
        assert note.duration == music.resolution * durations[i]
        assert note.pitch == pitches[i]


def test_piano_staff():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "43a-PianoStaff.xml")

    assert len(music.tracks) == 1

    notes = music.tracks[0].notes
    assert len(notes) == 2

    assert notes[0].start == 0
    assert notes[0].duration == music.resolution * 4
    assert notes[0].pitch == 47

    assert notes[1].start == 0
    assert notes[1].duration == music.resolution * 4
    assert notes[1].pitch == 65


def test_quoted_headers():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "51b-Header-Quotes.xml")

    assert music.metadata.title == '"Quotes" in header fields'
    assert music.metadata.creators == ['Some "Tester" Name']


def test_multiple_rights():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "51c-MultipleRights.xml")

    assert (
        music.metadata.copyright
        == "Copyright © XXXX by Y. ZZZZ. Released To The Public Domain."
    )


def test_empty_title():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "51d-EmptyTitle.xml")

    assert music.metadata.title == "Empty work-title, non-empty movement-title"


def test_transpose_instruments():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "72a-TransposingInstruments.xml"
    )

    assert len(music.tracks) == 3

    # Answers
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]

    for track in music.tracks:
        for note, pitch in zip(track.notes, pitches):
            assert note.pitch == pitch


def test_percussion():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "73a-Percussion.xml")

    assert len(music.tracks) == 3

    notes = music.tracks[0].notes
    assert len(notes) == 2

    assert notes[0].duration == music.resolution * 6
    assert notes[0].pitch == 52

    assert notes[1].duration == music.resolution * 2
    assert notes[1].pitch == 45

    assert len(music.tracks[1].notes) == 0
    assert len(music.tracks[2].notes) == 0


def test_compressed_musicxml():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "90a-Compressed-MusicXML.mxl"
    )

    assert music.metadata.title == "Compressed MusicXML file"
    assert len(music.tracks) == 1
    assert len(music.tracks[0].notes) == 4


def test_realworld():
    music = muspy.read(TEST_MUSICXML_DIR / "fur-elise.xml")

    assert music.metadata.creators == ["Ludwig van Beethoven"]
    assert music.metadata.source_filename == "fur-elise.xml"
    assert music.metadata.source_format == "musicxml"

    assert len(music.tracks) == 1

    assert len(music.tempos) == 1
    assert music.tempos[0].tempo == 72

    assert len(music.key_signatures) == 1
    assert music.key_signatures[0].root == "C"
    assert music.key_signatures[0].mode == "major"

    assert len(music.time_signatures) == 1
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8


def test_realworld_compressed():
    music = muspy.read(TEST_MUSICXML_DIR / "fur-elise.mxl")

    assert music.metadata.creators == ["Ludwig van Beethoven"]
    assert music.metadata.source_filename == "fur-elise.mxl"
    assert music.metadata.source_format == "musicxml"

    assert len(music.tracks) == 1

    assert len(music.tempos) == 1
    assert music.tempos[0].tempo == 72

    assert len(music.key_signatures) == 1
    assert music.key_signatures[0].root == "C"
    assert music.key_signatures[0].mode == "major"

    assert len(music.time_signatures) == 1
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8


def test_write():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.xml")

    loaded = muspy.read(temp_dir / "test.xml")

    assert loaded.metadata.title == "Fur Elise"
    assert loaded.metadata.source_filename == "test.xml"
    assert loaded.metadata.source_format == "musicxml"
    assert loaded.resolution == 10080
    print(loaded)
    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_lyrics(loaded.lyrics)
    check_tracks(loaded.tracks, 10080)


def test_write_compressed():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.mxl")

    loaded = muspy.read(temp_dir / "test.mxl")

    assert loaded.metadata.title == "Fur Elise"
    assert loaded.metadata.source_filename == "test.xml"
    assert loaded.metadata.source_format == "musicxml"
    assert loaded.resolution == 10080
    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_lyrics(loaded.lyrics)
    check_tracks(loaded.tracks, 10080)
