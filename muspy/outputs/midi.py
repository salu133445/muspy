"""MIDI output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

import numpy as np
from miditoolkit import Instrument as MtkInstrument
from miditoolkit import KeySignature as MtkKeySignature
from miditoolkit import Lyric as MtkLyric
from miditoolkit import Note as MtkNote
from miditoolkit import TempoChange as MtkTempo
from miditoolkit import TimeSignature as MtkTimeSignature
from miditoolkit.midi.parser import MidiFile as MtkMidiFile
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from pretty_midi import Instrument as PmInstrument
from pretty_midi import KeySignature as PmKeySignature
from pretty_midi import Lyric as PmLyric
from pretty_midi import Note as PmNote
from pretty_midi import PrettyMIDI
from pretty_midi import TimeSignature as PmTimeSignature
from pretty_midi import key_name_to_key_number

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
DEFAULT_TEMPO = 120


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
        "set_tempo", time=tempo.time, tempo=bpm2tempo(tempo.qpm)
    )


def to_mido_key_signature(
    key_signature: KeySignature,
) -> Optional[MetaMessage]:
    """Return a KeySignature object as a mido MetaMessage object.

    Timing is in absolute time, NOT in delta time.

    """
    # TODO: `key_signature.root_str` might be given
    if key_signature.root is None:
        return None
    if key_signature.mode not in ("major", "minor"):
        return None
    suffix = "m" if key_signature.mode == "minor" else ""
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
    note: Note, channel: int, use_note_off_message: bool = False
) -> Tuple[Message, Message]:
    """Return a Note object as mido Message objects.

    Timing is in absolute time, NOT in delta time.

    Parameters
    ----------
    note : :class:`muspy.Note` object
        Note object to convert.
    channel : int
        Channel of the MIDI message.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

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
    if use_note_off_message:
        note_off_msg = Message(
            "note_off",
            time=note.end,
            note=note.pitch,
            velocity=64,
            channel=channel,
        )
    else:
        note_off_msg = Message(
            "note_on",
            time=note.end,
            note=note.pitch,
            velocity=0,
            channel=channel,
        )

    return note_on_msg, note_off_msg


def to_mido_track(
    track: Track, channel: int = None, use_note_off_message: bool = False,
) -> MidiTrack:
    """Return a Track object as a mido MidiTrack object.

    Parameters
    ----------
    track : :class:`muspy.Track` object
        Track object to convert.
    channel : int, optional
        Channel number. Defaults to 10 for drums and 0 for other
        instruments.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

    Returns
    -------
    :class:`mido.MidiTrack` object
        Converted mido MidiTrack object.

    """
    if channel is None:
        channel = 9 if track.is_drum else 0

    # Create a new MIDI track
    midi_track = MidiTrack()

    # Track name messages
    if track.name is not None:
        midi_track.append(MetaMessage("track_name", name=track.name))

    # Program change messages
    midi_track.append(
        Message("program_change", program=track.program, channel=channel)
    )

    # Note on and note off messages
    for note in track.notes:
        midi_track.extend(
            to_mido_note_on_note_off(
                note,
                channel=channel,
                use_note_off_message=use_note_off_message,
            )
        )

    # End of track message
    midi_track.append(MetaMessage("end_of_track"))

    # Convert to delta time
    to_delta_time(midi_track)

    return midi_track


def to_mido(music: "Music", use_note_off_message: bool = False):
    """Return a Music object as a MidiFile object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

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
    for i, track in enumerate(music.tracks):
        # NOTE: Many softwares use the same instrument for messages of
        # the same channel in different tracks. Thus, we want to assign
        # a unique channel number for each track. MIDI has 15 channels
        # for instruments other than drums, so we increment the channel
        # number for each track (skipping the drum channel) and go back
        # to 0 once we run out of channels.

        # Assign channel number
        if track.is_drum:
            # Mido numbers channels 0 to 15 instead of 1 to 16
            channel = 9
        else:
            # MIDI has 15 channels for instruments other than drums
            channel = i % 15
            # Avoid drum channel
            if channel > 8:
                channel += 1

        midi.tracks.append(
            to_mido_track(
                track,
                channel=channel,
                use_note_off_message=use_note_off_message,
            )
        )

    return midi


def write_midi_mido(
    path: Union[str, Path], music: "Music", use_note_off_message: bool = False
):
    """Write a Music object to a MIDI file using mido as backend.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to write.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

    """
    midi = to_mido(music, use_note_off_message=use_note_off_message)
    midi.save(str(path))


def to_pretty_midi_key_signature(
    key_signature: KeySignature, map_time: Callable = None
) -> Optional[PmKeySignature]:
    """Return a KeySignature object as a pretty_midi KeySignature."""
    # TODO: `key_signature.root_str` might be given
    if key_signature.root is None:
        return None
    if key_signature.mode not in ("major", "minor"):
        return None
    key_name = f"{PITCH_NAMES[key_signature.root]} {key_signature.mode}"
    if map_time is not None:
        time = map_time(key_signature.time)
    else:
        time = key_signature.time
    return PmKeySignature(
        key_number=key_name_to_key_number(key_name), time=time
    )


def to_pretty_midi_time_signature(
    time_signature: TimeSignature, map_time: Callable = None
) -> PmTimeSignature:
    """Return a TimeSignature object as a pretty_midi TimeSignature."""
    if map_time is not None:
        time = map_time(time_signature.time)
    else:
        time = time_signature.time
    return PmTimeSignature(
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
        time=time,
    )


def to_pretty_midi_lyric(lyric: Lyric, map_time: Callable = None) -> PmLyric:
    """Return a Lyric object as a pretty_midi Lyric object."""
    if map_time is not None:
        time = map_time(lyric.time)
    else:
        time = lyric.time
    return PmLyric(text=lyric.lyric, time=time)


def to_pretty_midi_note(note: Note, map_time: Callable = None) -> PmNote:
    """Return a Note object as a pretty_midi Note object."""
    if map_time is not None:
        start = map_time(note.start)
        end = map_time(note.end)
    else:
        start = note.start
        end = note.end
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    return PmNote(velocity=velocity, pitch=note.pitch, start=start, end=end,)


def to_pretty_midi_instrument(
    track: Track, map_time: Callable = None
) -> PmInstrument:
    """Return a Track object as a pretty_midi Instrument object."""
    instrument = PmInstrument(
        program=track.program, is_drum=track.is_drum, name=track.name
    )
    for note in track.notes:
        instrument.notes.append(to_pretty_midi_note(note, map_time=map_time))
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

    Notes
    -----
    Tempo information will not be included in the output.

    """
    # Create an PrettyMIDI instance
    midi = PrettyMIDI()

    # Compute tempos
    tempo_times, tempi = [0], [float(DEFAULT_TEMPO)]
    for tempo in music.tempos:
        tempo_times.append(tempo.time)
        tempi.append(tempo.qpm)

    # Remove unnecessary tempo changes to speed up the search
    if len(tempi) > 1:
        last_tempo = tempi[0]
        last_time = tempo_times[0]
        i = 1
        while i < len(tempo_times):
            if tempi[i] == last_tempo:
                del tempo_times[i]
                del tempi[i]
            elif tempo_times[i] == last_time:
                del tempo_times[i - 1]
                del tempi[i - 1]
            else:
                last_tempo = tempi[i]
                i += 1

    if len(tempi) == 1:

        def map_time(time):
            return time * 60.0 / (music.resolution * tempi[0])

    else:
        tempo_times_np = np.array(tempo_times)
        tempi_np = np.array(tempi)

        # Compute the tempo time in absolute timing of each tempo change
        tempo_realtimes = np.cumsum(
            np.diff(tempo_times_np) * 60.0 / (music.resolution * tempi_np[:-1])
        ).tolist()
        tempo_realtimes.insert(0, 0.0)

        def map_time(time):
            idx = np.searchsorted(tempo_times_np, time, side="right") - 1
            residual = time - tempo_times_np[idx]
            factor = 60.0 / (music.resolution * tempi_np[idx])
            return tempo_realtimes[idx] + residual * factor

    # Key signatures
    for key_signature in music.key_signatures:
        pm_key_signature = to_pretty_midi_key_signature(
            key_signature, map_time
        )
        if pm_key_signature is not None:
            midi.key_signature_changes.append(pm_key_signature)

    # Time signatures
    for time_signature in music.time_signatures:
        midi.time_signature_changes.append(
            to_pretty_midi_time_signature(time_signature, map_time)
        )

    # Lyrics
    for lyric in music.lyrics:
        midi.lyrics.append(to_pretty_midi_lyric(lyric, map_time))

    # Tracks
    for track in music.tracks:
        midi.instruments.append(to_pretty_midi_instrument(track, map_time))

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

    Notes
    -----
    Tempo information will not be included in the output.

    """
    midi = to_pretty_midi(music)
    midi.write(str(path))


def write_midi(
    path: Union[str, Path],
    music: "Music",
    backend: str = "mido",
    **kwargs: Any,
):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music`
        Music object to write.
    backend: {'mido', 'pretty_midi'}, default: 'mido'
        Backend to use.

    See Also
    --------
    write_midi_mido :
        Write a Music object to a MIDI file using mido as backend.
    write_midi_pretty_midi :
        Write a Music object to a MIDI file using pretty_midi as
        backend.

    """
    if backend == "mido":
        return write_midi_mido(path, music, **kwargs)
    if backend == "pretty_midi":
        return write_midi_pretty_midi(path, music)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")


def to_miditoolkit_tempo(tempo: Tempo) -> Optional[MtkTempo]:
    """Return a Tempo object as a miditoolkit TempoChange."""
    return MtkTempo(tempo=tempo.qpm, time=tempo.time)


def to_miditoolkit_key_signature(
    key_signature: KeySignature,
) -> Optional[MtkKeySignature]:
    """Return a KeySignature object as a miditoolkit KeySignature."""
    # TODO: `key_signature.root_str` might be given
    if key_signature.root is None:
        return None
    if key_signature.mode not in ("major", "minor"):
        return None
    suffix = "m" if key_signature.mode == "minor" else ""
    return MtkKeySignature(
        key_name=PITCH_NAMES[key_signature.root] + suffix,
        time=key_signature.time,
    )


def to_miditoolkit_time_signature(
    time_signature: TimeSignature,
) -> MtkTimeSignature:
    """Return a TimeSignature object as a miditoolkit TimeSignature."""
    return MtkTimeSignature(
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
        time=time_signature.time,
    )


def to_miditoolkit_lyric(lyric: Lyric) -> MtkLyric:
    """Return a Lyric object as a miditoolkit Lyric object."""
    return MtkLyric(text=lyric.lyric, time=lyric.time)


def to_miditoolkit_note(note: Note) -> MtkNote:
    """Return a Note object as a miditoolkit Note object."""
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    return MtkNote(
        velocity=velocity, pitch=note.pitch, start=note.time, end=note.end
    )


def to_miditoolkit_instrument(track: Track) -> MtkInstrument:
    """Return a Track object as a miditoolkit Instrument object."""
    instrument = MtkInstrument(
        program=track.program, is_drum=track.is_drum, name=track.name
    )
    for note in track.notes:
        instrument.notes.append(to_miditoolkit_note(note))
    return instrument


def to_miditoolkit(music: "Music") -> MtkMidiFile:
    """Return a Music object as a miditoolkit object.

    Tempo changes are not supported yet.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.

    Returns
    -------
    :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    Notes
    -----
    Tempo information will not be included in the output.

    """
    # Create an PrettyMIDI instance
    midi = MtkMidiFile(ticks_per_beat=music.resolution)

    # Tempos
    for tempo in music.tempos:
        midi.tempo_changes.append(to_miditoolkit_tempo(tempo))

    # Key signatures
    for key_signature in music.key_signatures:
        mtk_key_signature = to_miditoolkit_key_signature(key_signature)
        if mtk_key_signature is not None:
            midi.key_signature_changes.append(mtk_key_signature)

    # Time signatures
    for time_signature in music.time_signatures:
        midi.time_signature_changes.append(
            to_miditoolkit_time_signature(time_signature)
        )

    # Lyrics
    for lyric in music.lyrics:
        midi.lyrics.append(to_miditoolkit_lyric(lyric))

    # Tracks
    for track in music.tracks:
        midi.instruments.append(to_miditoolkit_instrument(track))

    # Compute max tick
    midi.max_tick = music.get_end_time()

    return midi
