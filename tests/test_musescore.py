"""Test cases for MUSESCORE I/O."""
import math

import numpy as np
import pytest

import muspy
from muspy.inputs.musescore import MuseScoreWarning
from muspy.utils import CIRCLE_OF_FIFTHS, MODE_CENTERS

from .utils import TEST_MUSESCORE_DIR, TEST_MUSESCORE_LILYPOND_DIR


def check_legacy_version(music):
    assert len(music) == 1
    assert len(music[0]) == 8

    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    for note, pitch in zip(music[0], pitches):
        assert note.pitch == pitch
        assert note.duration == music.resolution


def test_legacy_version_v1():
    with pytest.warns(MuseScoreWarning):
        music = muspy.read(TEST_MUSESCORE_DIR / "v1.mscx")

    check_legacy_version(music)


def test_legacy_version_v2():
    with pytest.warns(MuseScoreWarning):
        music = muspy.read(TEST_MUSESCORE_DIR / "v2.mscx")

    check_legacy_version(music)


def test_pitches():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "01a-Pitches-Pitches.mscx"
    )

    assert len(music) == 1
    assert len(music[0]) == 102

    # Answers
    pitches = [43, 45, 47, 48]
    for octave in range(4):
        for pitch in [50, 52, 53, 55, 57, 59, 60]:
            pitches.append(12 * octave + pitch)

    # Without accidentals
    for i, note in enumerate(music[0][:32]):
        assert note.pitch == pitches[i]

    # With a sharp
    for i, note in enumerate(music[0][32:64]):
        assert note.pitch == pitches[i] + 1

    # With a flat
    for i, note in enumerate(music[0][64:96]):
        assert note.pitch == pitches[i] - 1

    # Double alterations
    assert music[0][96].pitch == 74
    assert music[0][97].pitch == 70
    for note in music[0][98:]:
        assert note.pitch == 73


def test_durations():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "03a-Rhythm-Durations.mscx"
    )

    assert music.resolution == 480
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
    for i, note in enumerate(music[0][:11]):
        assert note.duration == round(480 * durations[i])

    # With a dot
    for i, note in enumerate(music[0][11:22]):
        assert note.duration == round(480 * durations[i] * 1.5)

    # With double dots
    for i, note in enumerate(music[0][22:]):
        assert note.duration == round(480 * durations_double_dotted[i] * 1.75)


def test_custom_resolution():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "03a-Rhythm-Durations.mscx",
        resolution=120,
    )

    assert music.resolution == 120
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
    for i, note in enumerate(music[0][:11]):
        assert note.duration == round(120 * durations[i])

    # With a dot
    for i, note in enumerate(music[0][11:22]):
        assert note.duration == round(120 * durations[i] * 1.5)

    # With double dots
    for i, note in enumerate(music[0][22:]):
        assert note.duration == round(120 * durations_double_dotted[i] * 1.75)


def test_time_signatures():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "11a-TimeSignatures.mscx")

    assert len(music.time_signatures) == 10

    # Answers
    numerators = (4, 2, 3, 2, 3, 4, 5, 3, 6, 12)
    denominators = (4, 2, 2, 4, 4, 4, 4, 8, 8, 8)
    times = 4 + np.insert(
        np.cumsum(4 * np.array(numerators) / np.array(denominators)), 0, 0
    )

    for i, time_signature in enumerate(music.time_signatures):
        assert time_signature.time == int(music.resolution * times[i])
        assert time_signature.numerator == numerators[i]
        assert time_signature.denominator == denominators[i]


def test_compound_time_signatures():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "11c-TimeSignatures-CompoundSimple.mscx"
    )

    assert len(music.time_signatures) == 2
    assert music.time_signatures[0].numerator == 5
    assert music.time_signatures[0].denominator == 8
    assert music.time_signatures[1].numerator == 9
    assert music.time_signatures[1].denominator == 4


def test_key_signatures():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "13a-KeySignatures.mscx")

    assert len(music.key_signatures) == 30

    for i, key_signature in enumerate(music.key_signatures):
        if i % 2 == 0:
            assert key_signature.mode == "major"
        else:
            assert key_signature.mode == "minor"
        assert key_signature.fifths == i // 2 - 7

    for i, key_signature in enumerate(music.key_signatures):
        root, root_str = CIRCLE_OF_FIFTHS[
            MODE_CENTERS[key_signature.mode] + key_signature.fifths
        ]
        assert key_signature.root == root
        assert key_signature.root_str == root_str


def test_church_modes():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "13b-KeySignatures-ChurchModes.mscx"
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
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "21a-Chord-Basic.mscx")

    assert len(music[0]) == 2

    assert music[0][0].pitch == 65
    assert music[0][0].time == 0
    assert music[0][0].duration == music.resolution
    assert music[0][1].pitch == 69
    assert music[0][1].time == 0
    assert music[0][1].duration == music.resolution


def test_chords_and_durations():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "21c-Chords-ThreeNotesDuration.mscx"
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

    for i, note in enumerate(music[0]):
        assert note.pitch == pitches[i]
        assert note.duration == music.resolution * durations[i]


def test_pickup_measures():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "21e-Chords-PickupMeasures.mscx"
    )

    assert len(music[0]) == 6

    # Answers
    pitches = (72, 65, 69, 72, 69, 72)
    times = (0, 1, 1, 1, 2, 2)
    durations = (1, 1, 1, 1, 1, 1)

    for i, note in enumerate(music[0]):
        assert note.pitch == pitches[i]
        assert note.time == music.resolution * times[i]
        assert note.duration == music.resolution * durations[i]


def test_tuplets():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "23a-Tuplets.mscx")

    assert len(music[0]) == 30

    # Answers
    pitches = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84]
    pitches += pitches[::-1]
    durations = [
        round(music.resolution * 2 / 3),
        round(music.resolution * 2 / 3),
        music.resolution * 2 - round(music.resolution * 4 / 3),
    ] * 3
    durations += [round(music.resolution * 2 / 4)] * 4
    durations += [round(music.resolution * 1 / 4)] * 4
    durations += [round(music.resolution * 3 / 7)] * 6 + [
        music.resolution * 3 - round(music.resolution * 3 / 7) * 6
    ]
    durations += [round(music.resolution * 2 / 6)] * 6

    for note, pitch, duration in zip(music[0], pitches, durations):
        assert note.pitch == pitch
        assert note.duration == duration


def test_grace_notes():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "24a-GraceNotes.mscx")

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
        + [72, 74, 76]
        + [65, 72, 76]
        + [72, 75]
        + [68, 72, 73]
        + [72]
    )
    times = (
        [0, 0]
        + [1, 1, 1]
        + [2, 2]
        + [3, 3]
        + [4, 4]
        + [5, 5, 5]
        + [7, 7]
        + [7.5, 7.5, 7.5]
        + [8, 8, 8]
        + [9, 9]
        + [10, 10, 10]
        + [11]
    )
    durations = (
        [1, 0.25]
        + [1, 0.25, 0.25]
        + [1, 0.25]
        + [1, 0.5]
        + [1, 0.25]
        + [2, 0.25, 0.25]
        + [0.5, 0.25]
        + [0.5, 0.25, 0.25]
        + [1, 1, 0.25]
        + [1, 1]
        + [1, 1, 1]
        + [1]
    )

    for i, note in enumerate(music[0]):
        assert note.pitch == pitches[i]
        assert note.time == round(music.resolution * times[i])
        assert note.duration == round(music.resolution * durations[i])


def test_directions():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "31a-Directions.mscx")

    assert len(music.tempos) == 1
    assert music.tempos[0].time == 11 * 4 * music.resolution
    assert music.tempos[0].qpm == 60


def test_metronome():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "31c-MetronomeMarks.mscx")

    assert len(music.tempos) == 3

    # Answers
    qpms = (150, 1600, 115.5)

    for tempo, qpm in zip(music.tempos, qpms):
        assert math.isclose(tempo.qpm, qpm)


def test_ties():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "33b-Spanners-Tie.mscx")

    assert len(music[0]) == 1

    assert music[0][0].duration == music.resolution * 8
    assert music[0][0].pitch == 65


def test_ties_not_ended():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "33i-Ties-NotEnded.mscx")

    assert len(music[0]) == 2

    assert music[0][0].duration == music.resolution * 8
    assert music[0][0].pitch == 72
    assert music[0][1].duration == music.resolution * 12
    assert music[0][1].pitch == 72


def test_parts():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "41a-MultiParts-Partorder.mscx"
    )

    assert len(music) == 4

    # Answers
    pitches = [60, 64, 67, 71]

    for i, track in enumerate(music.tracks):
        assert track.name == "Part " + str(i + 1)
        assert track[0].time == 0
        assert track[0].duration == music.resolution
        assert track[0].pitch == pitches[i]


def test_part_names_with_line_breaks():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR
        / "41e-StaffGroups-InstrumentNames-Linebroken.mscx"
    )

    assert music[0].name == "Long Staff Name"


def test_voices():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR
        / "42a-MultiVoice-TwoVoicesOnStaff-Lyrics.mscx"
    )

    assert len(music) == 1
    assert len(music[0]) == 12

    # Answers
    times = (0, 0, 2, 2, 3, 3, 5, 5, 6, 6, 7.5, 7.5)
    pitches = (72, 76, 71, 74, 67, 71, 71, 74, 55, 59, 69, 72)
    durations = (2, 2, 1, 1, 1, 1, 1, 1, 1.5, 1.5, 0.5, 0.5)

    for i, note in enumerate(music[0]):
        assert note.time == music.resolution * times[i]
        assert note.duration == music.resolution * durations[i]
        assert note.pitch == pitches[i]


def test_lyrics():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR
        / "42a-MultiVoice-TwoVoicesOnStaff-Lyrics.mscx"
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
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "61a-Lyrics.mscx")

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
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "61e-Lyrics-Chords.mscx")

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
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "43a-PianoStaff.mscx")

    assert len(music) == 1
    assert len(music[0]) == 2

    assert music[0][0].time == 0
    assert music[0][0].duration == music.resolution * 4
    assert music[0][0].pitch == 47
    assert music[0][1].time == 0
    assert music[0][1].duration == music.resolution * 4
    assert music[0][1].pitch == 65


def test_repeat():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "45a-SimpleRepeat.mscx")
    assert len(music) == 1
    assert len(music[0]) == 6


def test_repeat_with_alternatives():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "45b-RepeatWithAlternatives.mscx"
    )
    assert len(music) == 1
    assert len(music[0]) == 5


def test_quoted_headers():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "51b-Header-Quotes.mscx")

    assert music.metadata.title == '"Quotes" in header fields'
    assert music.metadata.creators == ['Some "Tester" Name']


def test_multiple_rights():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "51c-MultipleRights.mscx")

    assert (
        music.metadata.copyright
        == "Copyright © XXXX by Y. ZZZZ. Released To The Public Domain."
    )


def test_empty_title():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "51d-EmptyTitle.mscx")

    assert music.metadata.title == "Empty work-title, non-empty movement-title"


def test_transpose_instruments():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "72a-TransposingInstruments.mscx"
    )

    assert len(music) == 3

    # Answers
    pitches = (60, 62, 64, 65, 67, 69, 71, 72)

    for track in music.tracks:
        for note, pitch in zip(track.notes, pitches):
            assert note.pitch == pitch


def test_percussion():
    music = muspy.read(TEST_MUSESCORE_LILYPOND_DIR / "73a-Percussion.mscx")

    assert len(music) == 3
    assert len(music[0]) == 2

    assert music[0][0].duration == music.resolution * 6
    assert music[0][0].pitch == 52
    assert music[0][1].duration == music.resolution * 2
    assert music[0][1].pitch == 45

    assert len(music[1]) == 3
    assert len(music[2]) == 3


def test_compressed_musescore():
    music = muspy.read(
        TEST_MUSESCORE_LILYPOND_DIR / "90a-Compressed-MuseScore.mscz"
    )

    assert music.metadata.title == "Compressed MuseScore file"
    assert len(music) == 1
    assert len(music[0]) == 4


def test_dcalfine():
    music = muspy.read(TEST_MUSESCORE_DIR / "dcalfine.mscx")

    assert len(music) == 1
    assert len(music[0]) == 6


def test_dsalfine():
    music = muspy.read(TEST_MUSESCORE_DIR / "dsalfine.mscx")

    assert len(music) == 1
    assert len(music[0]) == 6


def test_dsalcoda():
    music = muspy.read(TEST_MUSESCORE_DIR / "dsalcoda.mscx")

    assert len(music) == 1
    assert len(music[0]) == 5


def test_realworld():
    music = muspy.read(TEST_MUSESCORE_DIR / "fur-elise.mscx")

    assert music.metadata.creators == ["Ludwig van Beethoven(1770–1827)"]
    assert music.metadata.source_filename == "fur-elise.mscx"
    assert music.metadata.source_format == "musescore"

    assert len(music) == 1

    assert len(music.tempos) == 5  # Due to the repeat and ritardando
    assert music.tempos[0].qpm == 72

    assert len(music.key_signatures) == 0

    assert len(music.time_signatures) == 2  # Due to the repeat
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8

    assert len(music.barlines) == 127


def test_realworld_compressed():
    music = muspy.read(TEST_MUSESCORE_DIR / "fur-elise.mscz")

    assert music.metadata.creators == ["Ludwig van Beethoven(1770–1827)"]
    assert music.metadata.source_filename == "fur-elise.mscz"
    assert music.metadata.source_format == "musescore"

    assert len(music) == 1

    assert len(music.tempos) == 5  # Due to the repeat and ritardando
    assert music.tempos[0].qpm == 72

    assert len(music.key_signatures) == 0

    assert len(music.time_signatures) == 2  # Due to the repeat
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8

    assert len(music.barlines) == 127
