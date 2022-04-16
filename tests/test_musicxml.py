"""Test cases for MusicXML I/O."""
import tempfile
from pathlib import Path

import numpy as np

import muspy
from muspy.utils import CIRCLE_OF_FIFTHS, MODE_CENTERS

from .utils import (
    TEST_JSON_PATH,
    TEST_MUSICXML_DIR,
    TEST_MUSICXML_LILYPOND_DIR,
    check_key_signatures,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_pitches():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "01a-Pitches-Pitches.xml")

    assert len(music) == 1
    assert len(music[0]) == 102

    # Answers
    pitches = [43, 45, 47, 48]
    for octave in range(4):
        for pitch in [50, 52, 53, 55, 57, 59, 60]:
            pitches.append(12 * octave + pitch)

    # Without accidentals
    for note, pitch in zip(music[0], pitches):
        assert note.pitch == pitch

    # With a sharp
    for note, pitch in zip(music[0][32:64], pitches):
        assert note.pitch == pitch + 1

    # With a flat
    for note, pitch in zip(music[0][64:96], pitches):
        assert note.pitch == pitch - 1

    # Double alterations
    assert music[0][96].pitch == 74
    assert music[0][97].pitch == 70
    for note in music[0][98:]:
        assert note.pitch == 73


def test_durations():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "03a-Rhythm-Durations.xml")

    assert music.resolution == 64
    assert len(music) == 1
    assert len(music[0]) == 32

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
    durations_double_dotted = (
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
    )

    # Without dots
    for note, duration in zip(music[0][:11], durations):
        assert note.duration == 64 * duration

    # With a dot
    for note, duration in zip(music[0][11:22], durations):
        assert note.duration == 64 * duration * 1.5

    # With double dots
    for note, duration in zip(music[0][22:], durations_double_dotted):
        assert note.duration == 64 * duration * 1.75


def test_rhythm_backup():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "03b-Rhythm-Backup.xml")

    assert len(music) == 1
    assert len(music[0]) == 4

    # Answers
    times = [0, 1, 1, 2]
    pitches = [60, 57, 60, 57]

    for note, pitch, time in zip(music[0], pitches, times):
        assert note.time == time * music.resolution
        assert note.pitch == pitch


def test_divisions():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "03c-Rhythm-DivisionChange.xml"
    )

    assert music.resolution == 152
    assert len(music[0]) == 6
    assert music[0][0].duration == music.resolution
    assert music[0][4].duration == 2 * music.resolution


def test_custom_resolution():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "03c-Rhythm-DivisionChange.xml",
        resolution=24,
    )

    assert music.resolution == 24
    assert len(music[0]) == 6
    assert music[0][0].duration == music.resolution
    assert music[0][4].duration == 2 * music.resolution


def test_time_signatures():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "11a-TimeSignatures.xml")

    assert len(music.time_signatures) == 11

    # Answers
    numerators = (2, 4, 2, 3, 2, 3, 4, 5, 3, 6, 12)
    denominators = (2, 4, 2, 2, 4, 4, 4, 4, 8, 8, 8)
    times = np.insert(
        np.cumsum(4 * np.array(numerators) / np.array(denominators)), 0, 0
    )

    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.time == int(music.resolution * times[i])
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

    for i, key_signature in enumerate(music.key_signatures):
        if i % 2 == 0:
            assert key_signature.mode == "major"
        else:
            assert key_signature.mode == "minor"
        assert key_signature.fifths == i // 2 - 11

    for i, key_signature in enumerate(music.key_signatures[8:-4]):
        root, root_str = CIRCLE_OF_FIFTHS[
            MODE_CENTERS[key_signature.mode] + key_signature.fifths
        ]
        assert key_signature.root == root
        assert key_signature.root_str == root_str


def test_church_modes():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "13b-KeySignatures-ChurchModes.xml"
    )

    assert len(music.key_signatures) == 9

    # Answers
    modes = (
        "major",
        "minor",
        "ionian",
        "dorian",
        "phrygian",
        "lydian",
        "mixolydian",
        "aeolian",
        "locrian",
    )

    for key_signature, answer in zip(music.key_signatures, modes):
        assert key_signature.mode == answer
        # TODO: Check root and root_str


def test_chords():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "21a-Chord-Basic.xml")

    assert len(music[0]) == 2

    assert music[0][0].time == 0
    assert music[0][0].duration == music.resolution
    assert music[0][0].pitch == 65
    assert music[0][1].time == 0
    assert music[0][1].duration == music.resolution
    assert music[0][1].pitch == 69


def test_chords_and_durations():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "21c-Chords-ThreeNotesDuration.xml"
    )

    assert len(music[0]) == 20

    # Answers
    pitches = (
        [65, 69, 72]
        + [69, 79]
        + [65, 69, 72]
        + [65, 69, 72]
        + [65, 69, 76]
        + [65, 69, 77]
        + [65, 69, 74]
    )
    durations = [1.5, 1.5, 1.5] + [0.5, 0.5] + [1, 1, 1] * 4 + [2, 2, 2]

    for note, pitch, duration in zip(music[0], pitches, durations):
        assert note.duration == music.resolution * duration
        assert note.pitch == pitch


def test_pickup_measures():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "21e-Chords-PickupMeasures.xml"
    )

    assert len(music[0]) == 6

    # Answers
    times = (0, 1, 1, 1, 2, 2)
    pitches = (72, 65, 69, 72, 69, 72)
    durations = (1, 1, 1, 1, 1, 1)

    for i, note in enumerate(music[0]):
        assert note.time == times[i] * music.resolution
        assert note.duration == durations[i] * music.resolution
        assert note.pitch == pitches[i]


def test_tuplets():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "23a-Tuplets.xml")

    assert len(music[0]) == 30

    # Answers
    pitches = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84]
    pitches += pitches[::-1]
    durations = [2 / 3] * 9
    durations += [2 / 4] * 4
    durations += [1 / 4] * 4
    durations += [3 / 7] * 7
    durations += [2 / 6] * 6

    for note, pitch, duration in zip(music[0], pitches, durations):
        assert note.pitch == pitch
        assert note.duration == round(duration * music.resolution)


def test_grace_notes():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "24a-GraceNotes.xml")

    assert len(music[0]) == 28

    # Answers
    pitches = (
        [72, 74]
        + [72, 74, 76]
        + [72, 74]
        + [72, 74]
        + [72, 74]
        + [72, 74, 76]
        + [72, 74]
        + [72, 74]
        + [65]
        + [72, 76, 76]
        + [72, 75, 68]
        + [72, 73]
        + [72]
    )
    durations = (
        [1, 0.25]
        + [1, 0.25, 0.25]
        + [1, 0.25]
        + [1, 0.5]
        + [1, 0.25]
        + [2, 0.25, 0.25]
        + [0.5, 0.25]
        + [0.5, 0.25]
        + [1]
        + [1, 0.25, 0.25]
        + [1, 1]
        + [1, 1, 1]
        + [1]
    )

    for note, pitch, duration in zip(music[0], pitches, durations):
        assert note.pitch == pitch
        assert note.duration == round(music.resolution * duration)


def test_directions():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "31a-Directions.xml")

    assert len(music.tempos) == 1
    assert music.tempos[0].time == 11 * 4 * music.resolution
    assert music.tempos[0].qpm == 60


def test_metronome():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "31c-MetronomeMarks.xml")

    assert len(music.tempos) == 3

    # Answers
    qpms = (150, 1600, 115.5)

    for tempo, qpm in zip(music.tempos, qpms):
        assert tempo.qpm == qpm


def test_ties():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "33b-Spanners-Tie.xml")

    assert len(music[0]) == 1

    assert music[0][0].duration == music.resolution * 8
    assert music[0][0].pitch == 65


def test_ties_not_ended():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "33i-Ties-NotEnded.xml")

    assert len(music[0]) == 2

    assert music[0][0].duration == music.resolution * 8
    assert music[0][0].pitch == 72
    assert music[0][1].duration == music.resolution * 12
    assert music[0][1].pitch == 72


def test_parts():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "41a-MultiParts-Partorder.xml"
    )

    assert len(music) == 4

    # Answers
    pitches = [60, 64, 67, 71]

    for i, (track, pitch) in enumerate(zip(music, pitches)):
        assert track.name == "Part " + str(i + 1)
        assert track[0].time == 0
        assert track[0].duration == music.resolution
        assert track[0].pitch == pitch


def test_part_names_with_line_breaks():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR
        / "41e-StaffGroups-InstrumentNames-Linebroken.xml"
    )

    assert music[0].name == "Long Staff Name"


def test_part_without_id():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "41g-PartNoId.xml")

    assert music.resolution == 1
    assert len(music) == 1


def test_unlisted_parts():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "41h-TooManyParts.xml")

    assert len(music) == 1


def test_voices():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR
        / "42a-MultiVoice-TwoVoicesOnStaff-Lyrics.xml"
    )

    assert len(music) == 1
    assert len(music[0]) == 12

    # Answers
    pitches = (72, 76, 71, 74, 67, 71, 71, 74, 55, 59, 69, 72)
    times = (0, 0, 2, 2, 3, 3, 5, 5, 6, 6, 7.5, 7.5)
    durations = (2, 2, 1, 1, 1, 1, 1, 1, 1.5, 1.5, 0.5, 0.5)

    for i, note in enumerate(music[0]):
        assert note.time == times[i] * music.resolution
        assert note.duration == durations[i] * music.resolution
        assert note.pitch == pitches[i]


def test_lyrics():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR
        / "42a-MultiVoice-TwoVoicesOnStaff-Lyrics.xml"
    )

    assert len(music) == 1
    assert len(music[0]) == 12
    assert len(music[0].lyrics) == 12

    # Answers
    times = (0, 0, 2, 2, 3, 3, 5, 5, 6, 6, 7.5, 7.5)
    lyrics = (
        "This",
        "This",
        "is",
        "is",
        "the",
        "the",
        "lyrics",
        "lyrics",
        "of",
        "of",
        "Voice1",
        "Voice1",
    )

    for i, lyric in enumerate(music[0].lyrics):
        assert lyric.time == music.resolution * times[i]
        assert lyric.lyric == lyrics[i]


def test_lyrics_syllables():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "61a-Lyrics.xml")

    assert len(music) == 1
    assert len(music[0]) == 11
    assert len(music[0].lyrics) == 7

    # Answers
    times = (0, 1, 2, 3, 5, 7, 9)
    texts = ("Tra -", "- la -", "- li", "Ja!", "Tra -", "- ra!", "Bah!")

    for lyric, time, text in zip(music[0].lyrics, times, texts):
        assert lyric.time == music.resolution * time
        assert lyric.lyric == text


def test_lyrics_chords():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "61e-Lyrics-Chords.xml")

    assert len(music) == 1
    assert len(music[0]) == 8
    assert len(music[0].lyrics) == 4

    # Answers
    times = (0, 1, 2, 3)
    texts = ("Ly -", "- rics", "on", "chords")

    for lyric, time, text in zip(music[0].lyrics, times, texts):
        assert lyric.time == music.resolution * time
        assert lyric.lyric == text


def test_piano_staff():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "43a-PianoStaff.xml")

    assert len(music) == 1
    assert len(music[0]) == 2

    assert music[0][0].time == 0
    assert music[0][0].duration == music.resolution * 4
    assert music[0][0].pitch == 47
    assert music[0][1].time == 0
    assert music[0][1].duration == music.resolution * 4
    assert music[0][1].pitch == 65


def test_repeat():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "45a-SimpleRepeat.xml")

    assert len(music) == 1
    assert len(music[0]) == 6


def test_repeat_with_alternatives():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "45b-RepeatWithAlternatives.xml"
    )

    assert len(music) == 1
    assert len(music[0]) == 5


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

    assert len(music) == 3

    # Answers
    pitches = (60, 62, 64, 65, 67, 69, 71, 72)

    for track in music.tracks:
        for note, pitch in zip(track.notes, pitches):
            assert note.pitch == pitch


def test_percussion():
    music = muspy.read(TEST_MUSICXML_LILYPOND_DIR / "73a-Percussion.xml")

    assert len(music) == 3

    assert len(music[0]) == 2

    assert music[0][0].duration == music.resolution * 6
    assert music[0][0].pitch == 52
    assert music[0][1].duration == music.resolution * 2
    assert music[0][1].pitch == 45

    assert len(music[1]) == 3
    assert len(music[2]) == 3


def test_compressed_musicxml():
    music = muspy.read(
        TEST_MUSICXML_LILYPOND_DIR / "90a-Compressed-MusicXML.mxl"
    )

    assert music.metadata.title == "Compressed MusicXML file"
    assert len(music) == 1
    assert len(music[0]) == 4


def test_dcalfine():
    music = muspy.read(TEST_MUSICXML_DIR / "dcalfine.xml")

    assert len(music) == 1
    assert len(music[0]) == 6


def test_dsalfine():
    music = muspy.read(TEST_MUSICXML_DIR / "dsalfine.xml")

    assert len(music) == 1
    assert len(music[0]) == 6


def test_dsalcoda():
    music = muspy.read(TEST_MUSICXML_DIR / "dsalcoda.xml")

    assert len(music) == 1
    assert len(music[0]) == 5


def test_realworld():
    music = muspy.read(TEST_MUSICXML_DIR / "fur-elise.xml")

    assert music.metadata.creators == ["Ludwig van Beethoven"]
    assert music.metadata.source_filename == "fur-elise.xml"
    assert music.metadata.source_format == "musicxml"

    assert len(music) == 1

    assert len(music.tempos) == 2  # due to the repeats
    assert music.tempos[0].qpm == 72

    assert len(music.key_signatures) == 2  # due to the repeats
    assert music.key_signatures[0].fifths == 0

    assert len(music.time_signatures) == 2  # due to the repeats
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8

    assert len(music.barlines) == 127


def test_realworld_compressed():
    music = muspy.read(TEST_MUSICXML_DIR / "fur-elise.mxl")

    assert music.metadata.creators == ["Ludwig van Beethoven"]
    assert music.metadata.source_filename == "fur-elise.mxl"
    assert music.metadata.source_format == "musicxml"

    assert len(music) == 1

    assert len(music.tempos) == 2  # due to the repeats
    assert music.tempos[0].qpm == 72

    assert len(music.key_signatures) == 2  # due to the repeats
    assert music.key_signatures[0].fifths == 0

    assert len(music.time_signatures) == 2  # due to the repeats
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8

    assert len(music.barlines) == 127


def test_write():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.xml")

    loaded = muspy.read(temp_dir / "test.xml")

    assert loaded.metadata.title == "Für Elise"
    assert loaded.metadata.source_filename == "test.xml"
    assert loaded.metadata.source_format == "musicxml"
    assert loaded.resolution == 10080

    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_tracks(loaded.tracks, 10080)
    # TODO: Check lyrics and annotations


def test_write_compressed():
    music = muspy.load(TEST_JSON_PATH)

    temp_dir = Path(tempfile.mkdtemp())
    music.write(temp_dir / "test.mxl")

    loaded = muspy.read(temp_dir / "test.mxl")

    assert loaded.metadata.title == "Für Elise"
    assert loaded.metadata.source_filename == "test.mxl"
    assert loaded.metadata.source_format == "musicxml"
    assert loaded.resolution == 10080

    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_tracks(loaded.tracks, 10080)
    # TODO: Check lyrics and annotations
