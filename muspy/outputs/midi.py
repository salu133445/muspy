"""MIDI output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

import pretty_midi
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from pretty_midi import PrettyMIDI

if TYPE_CHECKING:
    from ..music import Music


def to_pretty_midi(music: "Music") -> PrettyMIDI:
    """Return a Music object as a PrettyMIDI object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    pm : :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    """
    pm = PrettyMIDI()

    pm.key_signature_changes = [
        pretty_midi.KeySignature(
            pretty_midi.key_name_to_key_number(
                "{} {}".format(key_signature.root, key_signature.mode)
            ),
            key_signature.time,
        )
        for key_signature in music.key_signatures
    ]

    pm.time_signature_changes = [
        pretty_midi.TimeSignature(
            time_signature.numerator,
            time_signature.denominator,
            time_signature.time,
        )
        for time_signature in music.time_signatures
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


def write_midi(music: "Music", path: Union[str, Path], backend: str = "mido"):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or Path
        Path to write the MIDI file.
    backend: {'mido', 'pretty_midi'}
        Backend to use.

    """
    if backend == "mido":
        return write_midi_mido(music, path)
    if backend == "pretty_midi":
        return write_midi_pretty_midi(music, path)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")


def write_midi_pretty_midi(music: "Music", path: Union[str, Path]):
    """Write a Music object to a MIDI file using pretty_midi as backend.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or Path
        Path to write the MIDI file.

    """
    pm = to_pretty_midi(music)
    pm.write(str(path))


def write_midi_mido(music: "Music", path: Union[str, Path]):
    """Write a Music object to a MIDI file using mido as backend.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or Path
        Path to write the MIDI file.

    """
    # Create a MIDI file object
    midi = MidiFile(type=1, ticks_per_beat=music.resolution)

    # Create a track to store the meta data
    meta_track = MidiTrack()
    midi.tracks.append(meta_track)

    # Tempos
    for tempo in music.tempos:
        meta_track.append(
            MetaMessage(
                "set_tempo", time=tempo.time, tempo=bpm2tempo(tempo.tempo),
            )
        )

    # Key signatures
    for key_signature in music.key_signatures:
        suffix = "m" if key_signature.mode == "minor" else ""
        meta_track.append(
            MetaMessage(
                "key_signature",
                time=key_signature.time,
                key=key_signature.root + suffix,
            )
        )

    # Time signatures
    for time_signature in music.time_signatures:
        meta_track.append(
            MetaMessage(
                "time_signature",
                time=time_signature.time,
                numerator=time_signature.numerator,
                denominator=time_signature.denominator,
            )
        )

    # Lyrics
    for lyric in music.lyrics:
        meta_track.append(
            MetaMessage("lyrics", time=lyric.time, text=lyric.lyric)
        )

    # Annotations
    for annotation in music.annotations:
        # Marker messages
        if annotation.group == "marker":
            meta_track.append(
                MetaMessage("marker", text=annotation.annotation)
            )
        # Text messages
        elif isinstance(annotation.annotation, str):
            meta_track.append(
                MetaMessage(
                    "text", time=annotation.time, text=annotation.annotation
                )
            )

    # Iterate over music tracks
    for track in music.tracks:

        # Create a new MIDI track
        midi_track = MidiTrack()
        midi.tracks.append(midi_track)

        # Track name messages
        if track.name is not None:
            midi_track.append(
                MetaMessage("track_name", time=0, name=track.name)
            )

        # Program change messages
        channel = 9 if track.is_drum else 0
        midi_track.append(
            Message(
                "program_change",
                time=0,
                program=track.program,
                channel=channel,
            )
        )

        # Note on and note off messages
        for note in track.notes:
            midi_track.append(
                Message(
                    "note_on",
                    time=note.start,
                    note=note.pitch,
                    velocity=int(note.velocity),
                    channel=channel,
                )
            )
            midi_track.append(
                Message(
                    "note_off",
                    time=note.end,
                    note=note.pitch,
                    velocity=int(note.velocity),
                    channel=channel,
                )
            )

    # Convert to delta time
    for midi_track in midi.tracks:
        # Sort messages by time
        midi_track.sort(key=lambda x: x.time)
        # Set current time to zero
        time = 0
        # Convert to delta time
        for msg in midi_track:
            time_ = msg.time
            msg.time -= time
            time = time_

    # Write to a MIDI file
    midi.save(str(path))
