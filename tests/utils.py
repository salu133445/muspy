"""Utility functions for testing."""
from math import isclose
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_JSON_PATH = TEST_DATA_DIR / "test.json"
TEST_YAML_PATH = TEST_DATA_DIR / "test.yaml"
TEST_JSON_GZ_PATH = TEST_DATA_DIR / "test.json.gz"
TEST_YAML_GZ_PATH = TEST_DATA_DIR / "test.yaml.gz"
TEST_MIDI_DIR = TEST_DATA_DIR / "midi"
TEST_MUSICXML_DIR = TEST_DATA_DIR / "musicxml"
TEST_MUSICXML_LILYPOND_DIR = TEST_DATA_DIR / "musicxml-lilypond"
TEST_MUSICXML_DIR = TEST_DATA_DIR / "musicxml"
TEST_MUSESCORE_DIR = TEST_DATA_DIR / "musescore"
TEST_MUSESCORE_LILYPOND_DIR = TEST_DATA_DIR / "musescore-lilypond"
TEST_ABC_DIR = TEST_DATA_DIR / "abc"


def check_metadata(metadata, ext=None):
    """Check metadata."""
    assert metadata.schema_version == "0.0"

    assert metadata.title == "Für Elise"
    assert len(metadata.creators) == 1
    assert metadata.creators[0] == "Ludwig van Beethoven"
    assert metadata.copyright is None

    assert metadata.collection == "Example dataset"
    if ext is not None:
        assert metadata.source_filename == "example." + ext
    assert metadata.source_format is None


def check_tempos(tempos, strict=True):
    """Check tempos."""
    assert len(tempos) == 1
    if strict:
        assert tempos[0].qpm == 72
    else:
        assert isclose(tempos[0].qpm, 72, rel_tol=1e-5)


def check_key_signatures(key_signatures):
    """Check key signatures."""
    assert len(key_signatures) == 1
    assert key_signatures[0].root == 9
    assert key_signatures[0].mode == "minor"


def check_time_signatures(time_signatures):
    """Check time signatures."""
    assert len(time_signatures) == 1
    assert time_signatures[0].numerator == 3
    assert time_signatures[0].denominator == 8


def check_barlines(barlines):
    """Check barlines."""
    assert len(barlines) == 3
    assert barlines[0].time == 0
    assert barlines[1].time == 12
    assert barlines[2].time == 48


def check_beats(beats):
    """Check beats."""
    assert len(beats) == 5
    times = [0, 12, 24, 36, 48]
    for beat, time in zip(beats, times):
        assert beat.time == time


def check_lyrics(lyrics):
    """Check lyrics."""
    assert len(lyrics) == 1
    assert lyrics[0].lyric == "Nothing but a lyric"


def check_annotations(annotations):
    """Check annotations."""
    assert len(annotations) == 1
    assert annotations[0].annotation == "Nothing but an annotation"
    assert annotations[0].group is None


def check_tracks(tracks, resolution=24):
    """Check tracks."""
    assert len(tracks) == 1
    assert tracks[0].program == 0
    assert not tracks[0].is_drum
    assert tracks[0].name == "Melody"

    notes = tracks[0].notes
    assert len(notes) == 9
    pitches = (76, 75, 76, 75, 76, 71, 74, 72, 69)
    for i, (note, pitch) in enumerate(zip(notes, pitches)):
        assert note.time == i * resolution // 4
        assert note.pitch == pitch
        assert note.duration == resolution // 4
        assert note.velocity == 64

    assert len(tracks[0].chords) == 0


def check_music(music, ext=None, resolution=24):
    """Check example music."""
    check_metadata(music.metadata, ext)
    assert music.resolution == resolution

    check_tempos(music.tempos)
    check_key_signatures(music.key_signatures)
    check_time_signatures(music.time_signatures)
    check_barlines(music.barlines)
    check_beats(music.beats)
    check_lyrics(music.lyrics)
    check_annotations(music.annotations)

    check_tracks(music.tracks, resolution=resolution)
    check_lyrics(music[0].lyrics)
    check_annotations(music[0].annotations)
