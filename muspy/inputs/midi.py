"""MIDI input interface."""
from pathlib import Path
from typing import Union

from pretty_midi import PrettyMIDI, key_number_to_key_name

from ..classes import (
    KeySignature,
    Lyric,
    MetaData,
    Note,
    TimeSignature,
    TimingInfo,
    Track,
)

from ..music import Music


def from_pretty_midi(pm: PrettyMIDI) -> Music:
    """Return a Music object converted from a PrettyMIDI object.

    Parameters
    ----------
    obj : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    time_signatures = [
        TimeSignature(
            time_signature.time,
            time_signature.numerator,
            time_signature.denominator,
        )
        for time_signature in pm.time_signature_changes
    ]

    key_signatures = [
        KeySignature(
            key_signature.time,
            key_number_to_key_name(key_signature.key_number).split()[0],
            key_number_to_key_name(key_signature.key_number).split()[1],
        )
        for key_signature in pm.key_signature_changes
    ]

    lyrics = [Lyric(lyric.time, lyric.text) for lyric in pm.lyrics]

    tracks = []
    for track in pm.tracks:
        notes = [
            Note(note.start, note.end, note.pitch, note.velocity)
            for note in track.notes
        ]
        tracks.append(Track(track.name, track.program, track.is_drum, notes))

    return Music(
        meta_data=MetaData(),
        timing_info=TimingInfo(False),
        time_signatures=time_signatures,
        key_signatures=key_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )


def read_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to be read.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    return from_pretty_midi(PrettyMIDI(str(path)))
