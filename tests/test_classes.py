"""Test cases for MusPy classes."""
import numpy as np
import pytest

from muspy import Metadata, Music, Note, Tempo, Track


def test_repr():
    note = Note(time=0, duration=1, pitch=60)
    assert repr(note) == "Note(time=0, pitch=60, duration=1, velocity=64)"


def test_from_dict():
    note = Note.from_dict({"time": 0, "duration": 1, "pitch": 60})
    assert note.time == 0
    assert note.duration == 1
    assert note.pitch == 60


def test_from_dict_strict():
    Note.from_dict(
        {"time": 0, "duration": 1, "pitch": 60}, strict=True,
    )


def test_from_dict_strict_error():
    with pytest.raises(TypeError):
        Note.from_dict(
            {"time": 0.0, "duration": "1", "pitch": np.int64([60])},
            strict=True,
        )


def test_from_dict_cast():
    note = Note.from_dict(
        {"time": 0.0, "duration": "1", "pitch": np.int64([60])}, cast=True
    )
    assert isinstance(note.time, int)
    assert isinstance(note.duration, int)
    assert isinstance(note.pitch, int)


def test_from_dict_cast_list_attributes():
    metadata = Metadata.from_dict(
        {"schema_version": "0.1", "creators": (1, True)}, cast=True
    )
    assert isinstance(metadata.creators, list)
    assert metadata.creators[0] == "1"
    assert metadata.creators[1] == "True"


def test_to_ordered_dict():
    note = Note(time=0, duration=1, pitch=60)
    ordered_dict = note.to_ordered_dict()
    assert ordered_dict["time"] == 0
    assert ordered_dict["duration"] == 1
    assert ordered_dict["pitch"] == 60


def test_fix_type():
    note = Note(time=0.0, duration="1", pitch=np.int64([60]))
    note.fix_type()
    assert isinstance(note.time, int)
    assert isinstance(note.duration, int)
    assert isinstance(note.pitch, int)


def test_fix_type2():
    tempo = Tempo(time=0.0, qpm=np.float64([72.0]))
    tempo.fix_type()
    assert isinstance(tempo.time, int)
    assert isinstance(tempo.qpm, float)


def test_fix_recursive():
    track = Track()
    track.append(Note(time=0.0, duration="1", pitch=np.int64([60])))
    track.append(Note(time=-1.0, duration="-1", pitch=np.int64([-1])))
    track.fix_type()
    assert isinstance(track[0].time, int)
    assert isinstance(track[0].duration, int)
    assert isinstance(track[0].pitch, int)


def test_append():
    track = Track()
    track.append(Note(time=0, duration=1, pitch=60))
    track.append(Note(time=1, duration=1, pitch=60))
    assert len(track) == 2


def test_extend():
    track = Track(notes=[Note(time=2, duration=1, pitch=60)])
    notes = [
        Note(time=1, duration=1, pitch=60),
        Note(time=2, duration=1, pitch=60),
    ]
    track.extend(notes)
    assert len(track) == 1 + len(notes)
    assert track[1:] == notes
    for a, b in zip(track[1:], notes):
        assert a is b


def test_extend_copy():
    track = Track(notes=[Note(time=2, duration=1, pitch=60)])
    notes = [
        Note(time=1, duration=1, pitch=60),
        Note(time=2, duration=1, pitch=60),
    ]
    track.extend(notes, deepcopy=True)
    assert track[1:] == notes
    for a, b in zip(track[1:], notes):
        assert a is not b


def test_iadd():
    track = Track(notes=[Note(time=2, duration=1, pitch=60)])
    notes = [
        Note(time=1, duration=1, pitch=60),
        Note(time=2, duration=1, pitch=60),
    ]
    track += notes
    assert track[1:] == notes
    for a, b in zip(track[1:], notes):
        assert a is b


def test_add_obj():
    track1 = Track(notes=[Note(time=0, duration=1, pitch=60)])
    track2 = Track(
        notes=[
            Note(time=1, duration=1, pitch=60),
            Note(time=2, duration=1, pitch=60),
        ]
    )
    merged = track1 + track2
    assert merged.notes == track1.notes + track2.notes
    for a, b in zip(merged.notes, track1.notes + track2.notes):
        assert a is not b


def test_remove_invalid():
    notes = [
        Note(time=-1, duration=1, pitch=60),
        Note(time=0, duration=1, pitch=60),
    ]
    track = Track(notes=notes)
    track.remove_invalid()
    assert len(track) == 1


def test_remove_invalid_recursive():
    notes = [
        Note(time=-1, duration=1, pitch=60),
        Note(time=0, duration=1, pitch=60),
    ]
    music = Music(tracks=[Track(notes=notes)])
    music.remove_invalid()
    assert len(music) == 1
    assert len(music[0]) == 1


def test_remove_duplicate():
    notes = [
        Note(time=0, duration=1, pitch=60),
        Note(time=0, duration=1, pitch=60),
    ]
    track = Track(notes=notes)
    track.remove_duplicate()
    assert len(track) == 1


def test_remove_duplicate_recursive():
    notes = [
        Note(time=0, duration=1, pitch=60),
        Note(time=0, duration=1, pitch=60),
    ]
    music = Music(tracks=[Track(notes=notes)])
    music.remove_duplicate()
    assert len(music) == 1
    assert len(music[0]) == 1


def test_ordering():
    notes = [
        Note(time=0, pitch=62, duration=1),
        Note(time=1, pitch=64, duration=1),
        Note(time=0, pitch=60, duration=1),
    ]
    assert notes[0] < notes[1]
    assert notes[1] > notes[2]
    assert not notes[0] < notes[2]

    notes.sort()
    assert notes[0].pitch == 62


def test_sort_track():
    notes = [
        Note(time=2, pitch=64, duration=1),
        Note(time=0, pitch=60, duration=1),
        Note(time=1, pitch=62, duration=1),
    ]
    track = Track(notes=notes)
    track.sort()

    # Answers
    times = (0, 1, 2)
    pitches = (60, 62, 64)

    assert len(track) == 3
    for i, note in enumerate(track):
        assert note.time == times[i]
        assert note.pitch == pitches[i]


def test_sort_music():
    notes = [
        Note(time=2, pitch=64, duration=1),
        Note(time=0, pitch=60, duration=1),
        Note(time=1, pitch=62, duration=1),
    ]
    music = Music(tracks=[Track(notes=notes)])
    music.sort()

    # Answers
    times = (0, 1, 2)
    pitches = (60, 62, 64)

    assert len(music[0]) == 3
    for i, note in enumerate(music[0]):
        assert note.time == times[i]
        assert note.pitch == pitches[i]
