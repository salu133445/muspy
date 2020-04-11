"""MIDI I/O utilities."""
from pathlib import Path
from typing import Union

import pretty_midi
from pretty_midi import (
    PrettyMIDI,
    key_number_to_key_name,
    key_name_to_key_number,
)

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

    music = Music(
        meta_data=MetaData(),
        timing_info=TimingInfo(False),
        time_signatures=time_signatures,
        key_signatures=key_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )

    return music


def read_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the MIDI file to be read.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    pm = PrettyMIDI(str(path))
    return from_pretty_midi(pm)


def to_pretty_midi(music: Music) -> PrettyMIDI:
    """Return a PrettyMIDI object converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    pm : :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    """
    if music.timing.is_symbolic_timing:
        raise NotImplementedError

    pm = PrettyMIDI()

    pm.time_signature_changes = [
        pretty_midi.TimeSignature(
            time_signature.numerator,
            time_signature.denominator,
            time_signature.time,
        )
        for time_signature in music.time_signatures
    ]

    pm.key_signature_changes = [
        pretty_midi.KeySignature(
            key_name_to_key_number(
                "{} {}".format(key_signature.root, key_signature.mode)
            ),
            key_signature.time,
        )
        for key_signature in music.key_signatures
    ]

    pm.lyrics = [
        pretty_midi.Lyric(lyric.lyric, lyric.time) for lyric in music.lyrics
    ]

    for track in music.tracks:
        instrument = pretty_midi.Instrument(
            track.program, track.is_drum, track.name
        )
        instrument.notes = [
            Note(note.start, note.end, note.pitch, note.velocity)
            for note in track.notes
        ]
        pm.instruments.append(instrument)

    return pm


def write_midi(music: Music, path: Union[str, Path]):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or :class:`pathlib.Path`
        Path to write the MIDI file.

    """
    pm = to_pretty_midi(music)
    pm.write(str(path))
