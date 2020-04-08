"""Utilities for I/O utilities."""
from collections import OrderedDict

from ..classes import (
    Annotation,
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SongInfo,
    SourceInfo,
    Tempo,
    TimeSignature,
    TimingInfo,
    Track,
)
from ..music import Music


def to_ordered_dict(music) -> OrderedDict:
    """Return an OrderedDict converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    OrderedDict
        Converted OrderedDict.

    """
    return music.to_ordered_dict()


def from_dict(data: dict) -> Music:
    """Return a Music object loaded from a dictionary.

    Parameters
    ----------
    data : dict
        Dictionary to be loaded.

    Returns
    -------
    music : :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    music = Music()

    # Global data
    music.timing = TimingInfo.from_dict(data["timing"])

    if data["time_signatures"] is not None:
        for time_signature in data["time_signatures"]:
            music.time_signatures.append(
                TimeSignature.from_dict(time_signature)
            )

    if data["key_signatures"] is not None:
        for key_signature in data["key_signatures"]:
            music.key_signatures.append(KeySignature.from_dict(key_signature))

    if data["tempos"] is not None:
        for tempo in data["tempos"]:
            music.tempos.append(Tempo.from_dict(tempo))

    if data["downbeats"] is not None:
        music.downbeats = data["downbeats"]

    if data["lyrics"] is not None:
        for lyric in data["lyrics"]:
            music.lyrics.append(Lyric.from_dict(lyric))

    if data["annotations"] is not None:
        for annotation in data["annotations"]:
            music.annotations.append(Annotation.from_dict(annotation))

    # Track-specific data
    music.tracks = []
    if data["tracks"] is not None:
        for track in data["tracks"]:
            notes, annotations, lyrics = [], [], []
            for note in track["notes"]:
                notes.append(Note.from_dict(note))
            for annotation in track["annotations"]:
                annotations.append(Annotation.from_dict(annotation))
            for lyric in track["lyrics"]:
                lyrics.append(Annotation(lyric["time"], lyric["lyric"]))
            music.tracks.append(
                Track(
                    track["name"],
                    track["program"],
                    track["is_drum"],
                    notes,
                    annotations,
                    lyrics,
                )
            )

    # Meta data
    song_info = SongInfo.from_dict(data["meta"]["song"],)
    source_info = SourceInfo.from_dict(data["meta"]["source"])
    music.meta = MetaData(
        data["meta"]["schema_version"], song_info, source_info
    )

    return music


def _from_dict(data: dict) -> Music:
    """Return a Music object loaded from a dictionary.

    Parameters
    ----------
    data : dict
        Dictionary to be loaded.

    Returns
    -------
    music : :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    music = Music()

    # Global data
    music.timing = TimingInfo(
        data["timing"]["is_symbolic_timing"],
        data["timing"]["beat_resolution"],
    )

    if data["time_signatures"] is not None:
        for time_signature in data["time_signatures"]:
            music.time_signatures.append(
                TimeSignature(
                    time_signature["time"],
                    time_signature["numerator"],
                    time_signature["denominator"],
                )
            )

    if data["key_signatures"] is not None:
        for key_signature in data["key_signatures"]:
            music.key_signatures.append(
                KeySignature(
                    key_signature["time"],
                    key_signature["root"],
                    key_signature["mode"],
                )
            )

    if data["tempos"] is not None:
        for tempo in data["tempos"]:
            music.tempos.append(Tempo(tempo["time"], tempo["tempo"]))

    if data["downbeats"] is not None:
        music.downbeats = data["downbeats"]

    if data["lyrics"] is not None:
        for lyric in data["lyrics"]:
            music.lyrics.append(Lyric(lyric["time"], lyric["lyric"]))

    if data["annotations"] is not None:
        for annotation in data["annotations"]:
            music.annotations.append(
                Annotation(annotation["time"], annotation["annotation"])
            )

    # Track-specific data
    music.tracks = []
    if data["tracks"] is not None:
        for track in data["tracks"]:
            notes, annotations, lyrics = [], [], []
            for note in track["notes"]:
                notes.append(
                    Note(
                        note["start"],
                        note["end"],
                        note["pitch"],
                        note["velocity"],
                    )
                )
            for annotation in track["annotations"]:
                annotations.append(
                    Annotation(annotation["time"], annotation["annotation"])
                )
            for lyric in track["lyrics"]:
                lyrics.append(Annotation(lyric["time"], lyric["lyric"]))
            music.tracks.append(
                Track(
                    track["name"],
                    track["program"],
                    track["is_drum"],
                    notes,
                    annotations,
                    lyrics,
                )
            )

    # Meta data
    song_info = SongInfo(
        data["meta"]["song"]["title"],
        data["meta"]["song"]["artist"],
        data["meta"]["song"]["composers"],
    )
    source_info = SourceInfo(
        data["meta"]["source"]["collection"],
        data["meta"]["source"]["filename"],
        data["meta"]["source"]["format"],
        data["meta"]["source"]["id"],
    )
    music.meta = MetaData(
        data["meta"]["schema_version"], song_info, source_info
    )

    return music
