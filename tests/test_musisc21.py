"""Test cases for music21 I/O."""
import muspy

from .utils import (
    TEST_JSON_PATH,
    check_key_signatures,
    check_lyrics,
    check_metadata,
    check_music,
    check_tempos,
    check_time_signatures,
    check_tracks,
)


def test_to_music21():
    music = muspy.load(TEST_JSON_PATH)

    score = muspy.to_music21(music)
    loaded = muspy.from_music21(score)

    assert loaded.metadata.title == "Fur Elise"
    assert loaded.resolution == 24

    check_tempos(loaded.tempos)
    check_key_signatures(loaded.key_signatures)
    check_time_signatures(loaded.time_signatures)
    check_lyrics(loaded.lyrics)
    check_tracks(loaded.tracks)
