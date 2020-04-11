"""Utilities for I/O utilities."""
from typing import Mapping
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


def to_ordered_dict(music: Music) -> OrderedDict:
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


def from_dict(data: Mapping) -> Music:
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

    # Meta data
    song_info = SongInfo.from_dict(data["meta"]["song"],)
    source_info = SourceInfo.from_dict(data["meta"]["source"])
    music.meta_data = MetaData(
        data["meta"]["schema_version"], song_info, source_info
    )

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

    return music
