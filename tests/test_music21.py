"""Test cases for music21 I/O."""
import music21

import muspy

from .utils import (
    TEST_JSON_PATH,
    TEST_MUSICXML_DIR,
    check_key_signatures,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_music21():
    music = muspy.load(TEST_JSON_PATH)

    score = muspy.to_object(music, "music21")
    loaded = muspy.from_object(score)

    assert loaded.metadata.title == "Für Elise"
    assert loaded.resolution == 24

    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_tracks(loaded.tracks, loaded.resolution)
    # TODO: Check lyrics and annotations


def test_music21_realworld():
    m21 = music21.converter.parse(TEST_MUSICXML_DIR / "fur-elise.xml")
    music = muspy.from_music21(m21)

    assert music.metadata.creators == ["Ludwig van Beethoven"]
    assert music.metadata.source_format == "music21"

    assert len(music) == 2

    assert len(music.tempos) == 1
    assert music.tempos[0].qpm == 120  # Music21 parse the tempo incorrectly

    assert len(music.key_signatures) == 2  # Due to the repeat
    assert music.key_signatures[0].fifths == 0

    assert len(music.time_signatures) == 2  # Due to the repeat
    assert music.time_signatures[0].numerator == 3
    assert music.time_signatures[0].denominator == 8
