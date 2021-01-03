"""Test cases for MusPy classes."""
from muspy import Music, Note, Track


def test_repr():
    note = Note(time=0, duration=1, pitch=60)
    assert repr(note) == "Note(time=0, pitch=60, duration=1, velocity=64)"


def test_from_dict():
    note = Note.from_dict({"time": 0, "duration": 1, "pitch": 60})
    assert note.time == 0
    assert note.duration == 1
    assert note.pitch == 60


def test_to_ordered_dict():
    note = Note(time=0, duration=1, pitch=60)
    ordered_dict = note.to_ordered_dict()
    assert ordered_dict["time"] == 0
    assert ordered_dict["duration"] == 1
    assert ordered_dict["pitch"] == 60


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
    assert track.notes[1:] == notes
    for a, b in zip(track.notes[1:], notes):
        assert a is b


def test_extend_copy():
    track = Track(notes=[Note(time=2, duration=1, pitch=60)])
    notes = [
        Note(time=1, duration=1, pitch=60),
        Note(time=2, duration=1, pitch=60),
    ]
    track.extend(notes, deepcopy=True)
    assert track.notes[1:] == notes
    for a, b in zip(track.notes[1:], notes):
        assert a is not b


def test_iadd():
    track = Track(notes=[Note(time=2, duration=1, pitch=60)])
    notes = [
        Note(time=1, duration=1, pitch=60),
        Note(time=2, duration=1, pitch=60),
    ]
    track += notes
    assert track.notes[1:] == notes
    for a, b in zip(track.notes[1:], notes):
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


def test_remove_duplicate():
    notes = [
        Note(time=0, duration=1, pitch=60),
        Note(time=0, duration=1, pitch=60),
    ]
    track = Track(notes=notes)
    track.remove_duplicate()
    assert len(track) == 1


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

    for i, note in enumerate(music.tracks[0]):
        assert note.time == times[i]
        assert note.pitch == pitches[i]
