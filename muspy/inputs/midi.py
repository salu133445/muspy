"""MIDI input interface."""
from collections import OrderedDict, defaultdict
from operator import attrgetter
from pathlib import Path
from typing import List, Union

from mido import MidiFile, tempo2bpm
from pretty_midi import Instrument
from pretty_midi import Note as PrettyMIDINote
from pretty_midi import PrettyMIDI

from ..classes import (
    Annotation,
    KeySignature,
    Lyric,
    Metadata,
    Note,
    Tempo,
    TimeSignature,
    Track,
)
from ..music import Music


class MIDIError(Exception):
    """An error class for MIDI related exceptions."""


def _is_drum(channel):
    return channel == 9


def from_mido(midi: MidiFile, duplicate_note_mode: str = "fifo") -> Music:
    """Return a Music object converted from a mido MidiFile object.

    Parameters
    ----------
    midi : :class:`mido.MidiFile` object
        MidiFile object to convert.
    duplicate_note_mode : {'fifo', 'lifo, 'close_all'}
        Policy for dealing with duplicate notes. When a note off message is
        presetned while there are multiple correspoding note on messages
        that have not yet been closed, we need a policy to decide which note
        on messages to close. Defaults to 'fifo'.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out):close the latest note on
        - 'close_all': close all note on messages

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    if duplicate_note_mode.lower() not in ("fifo", "lifo", "close_all"):
        raise ValueError(
            "`duplicate_note_mode` must be one of 'fifo', 'lifo' and "
            "'close_all'."
        )

    def _get_active_track(t_idx, program, channel):
        """Return the active track."""
        key = (program, channel)
        if key in tracks[t_idx]:
            return tracks[t_idx][key]
        tracks[t_idx][key] = Track(program, _is_drum(channel))
        return tracks[t_idx][key]

    # Raise MIDIError if the MIDI file is of Type 2 (i.e., asynchronous)
    if midi.type == 2:
        raise MIDIError("Type 2 MIDI file is not supported.")

    # Raise MIDIError if ticks_per_beat is not positive
    if midi.ticks_per_beat < 1:
        raise MIDIError("`ticks_per_beat` must be positive.")

    time = 0
    song_title = None
    tempos, key_signatures, time_signatures = [], [], []
    lyrics, annotations = [], []
    copyrights = []

    # Create a list to store converted tracks
    tracks: List[OrderedDict] = [
        OrderedDict() for _ in range(len(midi.tracks))
    ]
    # Create a list to store track names
    track_names = [None] * len(midi.tracks)

    # Iterate over MIDI tracks
    for track_idx, midi_track in enumerate(midi.tracks):

        # Set current time to zero
        time = 0
        # Keep track of the program used in each channel
        channel_programs = [0] * 16
        # Keep track of active note on messages
        active_notes = defaultdict(list)

        # Iterate over MIDI messages
        for msg in midi_track:

            # Update current time (delta time is used in a MIDI message)
            time += msg.time

            # === Meta Data ===

            # Tempo messages
            if msg.type == "set_tempo":
                tempos.append(Tempo(time=time, qpm=tempo2bpm(msg.tempo)))

            # Key signature messages
            elif msg.type == "key_signature":
                if msg.key.endswith("m"):
                    key_signatures.append(
                        KeySignature(
                            time=time, root=msg.key[:-1], mode="minor"
                        )
                    )
                else:
                    key_signatures.append(
                        KeySignature(time=time, root=msg.key, mode="major")
                    )

            # Time signature messages
            elif msg.type == "time_signature":
                time_signatures.append(
                    TimeSignature(
                        time=time,
                        numerator=msg.numerator,
                        denominator=msg.denominator,
                    )
                )

            # Lyric messages
            elif msg.type == "lyrics":
                lyrics.append(Lyric(time=time, lyric=msg.text))

            # Marker messages
            elif msg.type == "marker":
                annotations.append(
                    Annotation(time=time, annotation=msg.text, group="marker")
                )

            # Text messages
            elif msg.type == "text":
                annotations.append(
                    Annotation(time=time, annotation=msg.text, group="text")
                )

            # Copyright messages
            elif msg.type == "copyright":
                copyrights.append(msg.text)

            # === Track specific Data ===

            # Track name messages
            elif msg.type == "track_name":
                if midi.type == 0 or track_idx == 0:
                    song_title = msg.name
                else:
                    track_names[track_idx] = msg.name

            # Program change messages
            elif msg.type == "program_change":
                # Change program of the channel
                channel_programs[msg.channel] = msg.program

            # Note on messages
            elif msg.type == "note_on" and msg.velocity > 0:
                # A note on message will later be closed by a note off message
                active_notes[(msg.channel, msg.note)].append(
                    (time, msg.velocity)
                )

            # Note off messages
            # NOTE: A note on message with a zero velocity is also considered a
            # note off message
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                # Skip it if there is no active notes
                note_key = (msg.channel, msg.note)
                if not active_notes[note_key]:
                    continue

                # Get the active track
                program = channel_programs[msg.channel]
                track = _get_active_track(track_idx, program, msg.channel)

                # NOTE: There is no way to disambiguate duplicate notes (of
                # the same pitch on the same channel). Thus, we need a policy
                # for duplicate mode.

                # 'FIFO': (first in first out) close the earliest note
                if duplicate_note_mode.lower() == "fifo":
                    onset, velocity = active_notes[note_key][0]
                    track.notes.append(
                        Note(onset, time - onset, msg.note, velocity)
                    )
                    del active_notes[note_key][0]

                # 'LIFO': (last in first out) close the latest note on
                elif duplicate_note_mode.lower() == "lifo":
                    onset, velocity = active_notes[note_key][-1]
                    track.notes.append(
                        Note(onset, time - onset, msg.note, velocity)
                    )
                    del active_notes[note_key][-1]

                # 'close_all' - close all note on messages
                elif duplicate_note_mode.lower() in ("close_all", "close all"):
                    for onset, velocity in active_notes[note_key]:
                        track.notes.append(
                            Note(onset, time - onset, msg.note, velocity)
                        )
                    del active_notes[note_key]

            # End of track message
            elif msg.type == "end_of_track":
                break

        # Close all active notes
        for (channel, note), note_ons in active_notes.items():
            program = channel_programs[channel]
            track = _get_active_track(track_idx, program, channel)
            for onset, velocity in note_ons:
                track.notes.append(Note(onset, time - onset, note, velocity))

    music_tracks = []
    for track, track_name in zip(tracks, track_names):
        for sub_track in track.values():
            sub_track.name = track_name
        music_tracks.extend(track.values())

    # Sort notes
    for music_track in music_tracks:
        music_track.notes.sort(
            key=attrgetter("time", "pitch", "duration", "velocity")
        )

    # Meta data
    metadata = Metadata(
        title=song_title,
        source_format="midi",
        copyright=" ".join(copyrights) if copyrights else None,
    )

    return Music(
        metadata=metadata,
        resolution=midi.ticks_per_beat,
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=music_tracks,
    )


def read_midi_mido(
    path: Union[str, Path], duplicate_note_mode: str = "fifo"
) -> Music:
    """Read a MIDI file into a Music object using mido as backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to read.
    duplicate_note_mode : {'fifo', 'lifo, 'close_all'}
        Policy for dealing with duplicate notes. When a note off message is
        presetned while there are multiple correspoding note on messages
        that have not yet been closed, we need a policy to decide which note
        on messages to close. Defaults to 'fifo'.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out):close the latest note on
        - 'close_all': close all note on messages

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    midi = MidiFile(filename=str(path))
    music = from_mido(midi, duplicate_note_mode=duplicate_note_mode)
    music.metadata.source_filename = Path(path).name
    return music


def parse_pretty_midi_key_signatures(midi: PrettyMIDI) -> List[KeySignature]:
    """Return KeySignature objects parsed from a PrettyMIDI object.

    Parameters
    ----------
    midi : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to convert.

    Returns
    -------
    list of :class:`muspy.KeySignature` objects
        Converted key signatures.

    """
    key_signatures = []
    for key_signature in midi.key_signature_changes:
        is_minor, root = divmod(key_signature.key_number, 12)
        mode = "minor" if is_minor else "major"
        key_signatures.append(KeySignature(key_signature.time, root, mode))
    return key_signatures


def parse_pretty_midi_time_signatures(midi: PrettyMIDI) -> List[TimeSignature]:
    """Return TimeSignature objects parsed from a PrettyMIDI object.

    Parameters
    ----------
    midi : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to convert.

    Returns
    -------
    list of :class:`muspy.TimeSignature` objects
        Converted time signatures.

    """
    time_signatures = []
    for time_signature in midi.time_signature_changes:
        time_signatures.append(
            TimeSignature(
                time_signature.time,
                time_signature.numerator,
                time_signature.denominator,
            )
        )
    return time_signatures


def parse_pretty_midi_lyrics(midi: PrettyMIDI) -> List[Lyric]:
    """Return Lyric objects parsed from a PrettyMIDI object.

    Parameters
    ----------
    midi : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to convert.

    Returns
    -------
    list of :class:`muspy.Lyric` objects
        Converted lyrics.

    """
    return [Lyric(lyric.time, lyric.text) for lyric in midi.lyrics]


def parse_pretty_midi_note(note: PrettyMIDINote) -> Note:
    """Return a Note object parsed from a pretty_midi Note object.

    Parameters
    ----------
    note : :class:`pretty_midi.Note` object
        pretty_midi Note object to convert.

    Returns
    -------
    :class:`muspy.Note` object
        Converted note.

    """
    return Note(note.start, note.duration, note.pitch, note.velocity)


def parse_pretty_midi_instrument(instrument: Instrument) -> Track:
    """Return a Track object parsed from a pretty_midi Instrument object.

    Parameters
    ----------
    instrument : :class:`pretty_midi.Instrument` object
        pretty_midi Instrument object to convert.

    Returns
    -------
    :class:`muspy.Track` object
        Converted track.

    """
    notes = [parse_pretty_midi_note(note) for note in instrument.notes]
    return Track(
        instrument.program, instrument.is_drum, instrument.name, notes
    )


def from_pretty_midi(midi: PrettyMIDI) -> Music:
    """Return a Music object converted from a pretty_midi PrettyMIDI object.

    Parameters
    ----------
    midi : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to convert.

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    key_signatures = parse_pretty_midi_key_signatures(midi)
    time_signatures = parse_pretty_midi_time_signatures(midi)
    lyrics = parse_pretty_midi_lyrics(midi)
    tracks = [parse_pretty_midi_instrument(track) for track in midi.tracks]
    return Music(
        metadata=Metadata(source_format="midi"),
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )


def read_midi_pretty_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object using pretty_midi as backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to read.

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    music = from_pretty_midi(PrettyMIDI(str(path)))
    music.metadata.source_filename = Path(path).name
    return music


def read_midi(
    path: Union[str, Path],
    backend: str = "mido",
    duplicate_note_mode: str = "fifo",
) -> Music:
    """Read a MIDI file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to read.
    backend: {'mido', 'pretty_midi'}
        Backend to use.
    duplicate_note_mode : {'fifo', 'lifo, 'close_all'}
        Policy for dealing with duplicate notes. When a note off message is
        presetned while there are multiple correspoding note on messages
        that have not yet been closed, we need a policy to decide which note
        on messages to close. Defaults to 'fifo'. Only used when
        `backend='mido'`.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out):close the latest note on
        - 'close_all': close all note on messages

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    if backend == "mido":
        return read_midi_mido(path, duplicate_note_mode)
    if backend == "pretty_midi":
        return read_midi_pretty_midi(path)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")
