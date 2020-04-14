"""MIDI output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

import pretty_midi
from pretty_midi import PrettyMIDI

if TYPE_CHECKING:
    from ..music import Music


def to_pretty_midi(music: "Music") -> PrettyMIDI:
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
            pretty_midi.key_name_to_key_number(
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
            pretty_midi.Note(note.velocity, note.pitch, note.start, note.end)
            for note in track.notes
        ]
        pm.instruments.append(instrument)

    return pm


def write_midi(music: "Music", path: Union[str, Path]):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or Path
        Path to write the MIDI file.

    """
    pm = to_pretty_midi(music)
    pm.write(str(path))
