"""Utility functions for testing."""
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_JSON_PATH = TEST_DATA_DIR / "test.json"
TEST_YAML_PATH = TEST_DATA_DIR / "test.yaml"
TEST_MIDI_DIR = TEST_DATA_DIR / "midi"
TEST_MUSICXML_DIR = TEST_DATA_DIR / "musicxml"
TEST_MUSICXML_LILYPOND_DIR = TEST_DATA_DIR / "musicxml-lilypond"
TEST_ABC_DIR = TEST_DATA_DIR / "abc"


def check_metadata(metadata, ext=None):
    """Check metadata."""
    assert metadata.schema_version == "0.0"

    assert metadata.title == "Fur Elise"
    assert len(metadata.creators) == 1
    assert metadata.creators[0] == "Ludwig van Beethoven"
    assert metadata.copyright is None

    assert metadata.collection == "Example dataset"
    if ext is not None:
        assert metadata.source_filename == "example." + ext
    assert metadata.source_format is None


def check_tempos(tempos):
    """Check tempos."""
    assert len(tempos) == 1
    assert tempos[0].qpm == 72


def check_key_signatures(key_signatures):
    """Check key signatures."""
    assert len(key_signatures) == 1
    assert key_signatures[0].root == "A"
    assert key_signatures[0].mode == "minor"


def check_time_signatures(time_signatures):
    """Check time signatures."""
    assert len(time_signatures) == 1
    assert time_signatures[0].numerator == 3
    assert time_signatures[0].denominator == 8


def check_downbeats(downbeats):
    """Check downbeats."""
    assert len(downbeats) == 2
    assert downbeats[0] == 4
    assert downbeats[1] == 16


def check_lyrics(lyrics):
    """Check lyrics."""
    assert len(lyrics) == 1
    assert lyrics[0].lyric == "Nothing but a lyric"


def check_annotations(annotations):
    """Check annotations."""
    assert len(annotations) == 1
    assert annotations[0].annotation == "Nothing but an annotation"
    assert annotations[0].group is None


def check_tracks(tracks, resolution=4):
    """Check tracks."""
    assert len(tracks) == 1
    assert tracks[0].program == 0
    assert not tracks[0].is_drum
    assert tracks[0].name == "Melody"

    notes = tracks[0].notes
    assert len(notes) == 9
    for note, pitch in zip(notes, [76, 75, 76, 75, 76, 71, 74, 72, 69]):
        assert note.pitch == pitch
        assert note.duration == resolution // 2
        assert note.velocity == 64

    assert len(tracks[0].chords) == 0

    assert len(tracks[0].lyrics) == 1
    assert tracks[0].lyrics[0].lyric == "Nothing but a lyric"

    assert len(tracks[0].annotations) == 1
    assert tracks[0].annotations[0].annotation == "Nothing but an annotation"
    assert tracks[0].annotations[0].group is None


def check_music(music, ext=None, resolution=4):
    """Check example music."""
    check_metadata(music.metadata, ext)
    assert music.resolution == resolution
    check_tempos(music.tempos)
    check_key_signatures(music.key_signatures)
    check_time_signatures(music.time_signatures)
    check_downbeats(music.downbeats)
    check_lyrics(music.lyrics)
    check_annotations(music.annotations)
    check_tracks(music.tracks, resolution=resolution)
