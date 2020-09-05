"""MIDI output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

import pretty_midi
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from pretty_midi import Instrument
from pretty_midi import KeySignature as PmKeySignature
from pretty_midi import Lyric as PmLyric
from pretty_midi import Note as PmNote
from pretty_midi import PrettyMIDI
from pretty_midi import TimeSignature as PmTimeSignature

from ..classes import (
    DEFAULT_VELOCITY,
    KeySignature,
    Lyric,
    Note,
    Tempo,
    TimeSignature,
    Track,
)

if TYPE_CHECKING:
    from ..music import Music

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def to_delta_time(midi_track: MidiTrack):
    """Convert a mido MidiTrack object from absolute time to delta time.

    Parameters
    ----------
    midi_track : :class:`mido.MidiTrack` object
        mido MidiTrack object to convert.

    """
    # Sort messages by absolute time
    midi_track.sort(key=lambda x: x.time)

    # Convert to delta time
    time = 0
    for msg in midi_track:
        time_ = msg.time
        msg.time -= time
        time = time_


def to_mido_tempo(tempo: Tempo) -> MetaMessage:
    """Return a Tempo object as a mido MetaMessage object.

    Timing is in absolute time, NOT in delta time.

    """
    return MetaMessage(
        "set_tempo", time=tempo.time, tempo=bpm2tempo(tempo.qpm),
    )


def to_mido_key_signature(
    key_signature: KeySignature,
) -> Optional[MetaMessage]:
    """Return a KeySignature object as a mido MetaMessage object.

    Timing is in absolute time, NOT in delta time.

    """
    suffix = "m" if key_signature.mode == "minor" else ""
    if key_signature.root is None:
        return None
    return MetaMessage(
        "key_signature",
        time=key_signature.time,
        key=PITCH_NAMES[key_signature.root] + suffix,
    )


def to_mido_time_signature(time_signature: TimeSignature) -> MetaMessage:
    """Return a TimeSignature object as a mido MetaMessage object.

    Timing is in absolute time, NOT in delta time.

    """
    return MetaMessage(
        "time_signature",
        time=time_signature.time,
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
    )


def to_mido_meta_track(music: "Music") -> MidiTrack:
    """Return a mido MidiTrack containing metadata of a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.

    Returns
    -------
    :class:`mido.MidiTrack` object
        Converted mido MidiTrack object.

    """
    # Create a track to store the metadata
    meta_track = MidiTrack()

    # Song title
    if music.metadata.title is not None:
        meta_track.append(MetaMessage("track_name", name=music.metadata.title))

    # Tempos
    for tempo in music.tempos:
        meta_track.append(to_mido_tempo(tempo))

    # Key signatures
    for key_signature in music.key_signatures:
        mido_key_signature = to_mido_key_signature(key_signature)
        if mido_key_signature is not None:
            meta_track.append(mido_key_signature)

    # Time signatures
    for time_signature in music.time_signatures:
        meta_track.append(to_mido_time_signature(time_signature))

    # Lyrics
    for lyric in music.lyrics:
        meta_track.append(to_mido_lyric(lyric))

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

    # End of track message
    meta_track.append(MetaMessage("end_of_track"))

    # Convert to delta time
    to_delta_time(meta_track)

    return meta_track


def to_mido_lyric(lyric: Lyric) -> MetaMessage:
    """Return a Lyric object as a mido MetaMessage object.

    Timing is in absolute time, NOT in delta time.

    """
    return MetaMessage("lyrics", time=lyric.time, text=lyric.lyric)


def to_mido_note_on_note_off(
    note: Note, channel: int, use_note_on_as_note_off: bool = True
) -> Tuple[Message, Message]:
    """Return a Note object as mido Message objects.

    Timing is in absolute time, NOT in delta time.

    Parameters
    ----------
    note : :class:`muspy.Note` object
        Note object to convert.
    channel : int
        Channel of the MIDI message.
    use_note_on_as_note_off : bool
        Whether to use a note on message with zero velocity instead of a
        note off message. Defaults to True.

    Returns
    -------
    :class:`mido.Message` object
        Converted mido Message object for note on.
    :class:`mido.Message` object
        Converted mido Message object for note off.

    """
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    note_on_msg = Message(
        "note_on",
        time=note.time,
        note=note.pitch,
        velocity=velocity,
        channel=channel,
    )
    if use_note_on_as_note_off:
        note_off_msg = Message(
            "note_on",
            time=note.end,
            note=note.pitch,
            velocity=0,
            channel=channel,
        )
    else:
        note_off_msg = Message(
            "note_off",
            time=note.end,
            note=note.pitch,
            velocity=velocity,
            channel=channel,
        )

    return note_on_msg, note_off_msg


def to_mido_track(
    track: Track, use_note_on_as_note_off: bool = True
) -> MidiTrack:
    """Return a Track object as a mido MidiTrack object.

    Parameters
    ----------
    track : :class:`muspy.Track` object
        Track object to convert.
    use_note_on_as_note_off : bool
        Whether to use a note on message with zero velocity instead of a
        note off message.

    Returns
    -------
    :class:`mido.MidiTrack` object
        Converted mido MidiTrack object.

    """
    # Create a new MIDI track
    midi_track = MidiTrack()

    # Track name messages
    if track.name is not None:
        midi_track.append(MetaMessage("track_name", name=track.name))

    # Program change messages
    channel = 9 if track.is_drum else 0
    midi_track.append(
        Message("program_change", program=track.program, channel=channel,)
    )

    # Note on and note off messages
    for note in track.notes:
        midi_track.extend(
            to_mido_note_on_note_off(note, channel, use_note_on_as_note_off)
        )

    # End of track message
    midi_track.append(MetaMessage("end_of_track"))

    # Convert to delta time
    to_delta_time(midi_track)

    return midi_track


def to_mido(music: "Music", use_note_on_as_note_off: bool = True):
    """Return a Music object as a MidiFile object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    use_note_on_as_note_off : bool
        Whether to use a note on message with zero velocity instead of a
        note off message.

    Returns
    -------
    :class:`mido.MidiFile`
        Converted MidiFile object.

    """
    # Create a MIDI file object
    midi = MidiFile(type=1, ticks_per_beat=music.resolution)

    # Append meta track
    midi.tracks.append(to_mido_meta_track(music))

    # Iterate over music tracks
    for track in music.tracks:
        midi.tracks.append(to_mido_track(track, use_note_on_as_note_off))

    return midi


def write_midi_mido(
    path: Union[str, Path],
    music: "Music",
    use_note_on_as_note_off: bool = True,
):
    """Write a Music object to a MIDI file using mido as backend.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to write.
    use_note_on_as_note_off : bool
        Whether to use a note on message with zero velocity instead of a
        note off message.

    """
    midi = to_mido(music, use_note_on_as_note_off=use_note_on_as_note_off)
    midi.save(str(path))


def to_pretty_midi_key_signature(
    key_signature: KeySignature,
) -> PmKeySignature:
    """Return a KeySignature object as a pretty_midi KeySignature object."""
    return PmKeySignature(
        pretty_midi.key_name_to_key_number(
            "{} {}".format(key_signature.root, key_signature.mode)
        ),
        key_signature.time,
    )


def to_pretty_midi_time_signature(
    time_signature: TimeSignature,
) -> PmTimeSignature:
    """Return a KeySignature object as a pretty_midi TimeSignature object."""
    return PmTimeSignature(
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
        time=time_signature.time,
    )


def to_pretty_midi_lyric(lyric: Lyric) -> PmLyric:
    """Return a Lyric object as a pretty_midi Lyric object."""
    return PmLyric(lyric.lyric, lyric.time)


def to_pretty_midi_note(note: Note) -> PmNote:
    """Return a Note object as a pretty_midi Note object."""
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    return PmNote(
        velocity=velocity, pitch=note.pitch, start=note.time, end=note.end
    )


def to_pretty_midi_instrument(track: Track) -> Instrument:
    """Return a Track object as a pretty_midi Instrument object."""
    instrument = Instrument(
        program=track.program, is_drum=track.is_drum, name=track.name
    )
    for note in track.notes:
        instrument.notes.append(to_pretty_midi_note(note))
    return instrument


def to_pretty_midi(music: "Music") -> PrettyMIDI:
    """Return a Music object as a PrettyMIDI object.

    Tempo changes are not supported yet.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.

    Returns
    -------
    :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    """
    # Create an PrettyMIDI instance
    midi = PrettyMIDI()

    # Key signatures
    for key_signature in music.key_signatures:
        midi.key_signature_changes.append(
            to_pretty_midi_key_signature(key_signature)
        )

    # Time signatures
    for time_signature in music.time_signatures:
        midi.time_signature_changes.append(
            to_pretty_midi_time_signature(time_signature)
        )

    # Lyrics
    for lyric in music.lyrics:
        midi.lyrics.append(to_pretty_midi_lyric(lyric))

    # Tracks
    for track in music.tracks:
        midi.instruments.append(to_pretty_midi_instrument(track))

    # TODO: Adjust timings

    return midi


def write_midi_pretty_midi(path: Union[str, Path], music: "Music"):
    """Write a Music object to a MIDI file using pretty_midi as backend.

    Tempo changes are not supported yet.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to convert.

    """
    midi = to_pretty_midi(music)
    midi.write(str(path))


def write_midi(
    path: Union[str, Path],
    music: "Music",
    backend: str = "mido",
    **kwargs: Any
):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to write.
    backend: {'mido', 'pretty_midi'}
        Backend to use. Defaults to 'mido'.

    """
    if backend == "mido":
        return write_midi_mido(path, music, **kwargs)
    if backend == "pretty_midi":
        return write_midi_pretty_midi(path, music)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")
