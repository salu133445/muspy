"""MIDI input interface."""
from collections import OrderedDict, defaultdict
from operator import attrgetter
from pathlib import Path
from typing import List, Union

from mido import MidiFile, tempo2bpm
from pretty_midi import PrettyMIDI, key_number_to_key_name

from ..classes import (
    Annotation,
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SourceInfo,
    Tempo,
    TimeSignature,
    Track,
)
from ..music import Music


class MIDIError(Exception):
    """An error class for MIDI related exceptions."""


def _is_drum(channel):
    return channel == 9


def from_pretty_midi(pm: PrettyMIDI) -> Music:
    """Return a Music object converted from a pretty_midi PrettyMIDI object.

    Parameters
    ----------
    obj : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    key_signatures = [
        KeySignature(
            key_signature.time,
            key_number_to_key_name(key_signature.key_number).split()[0],
            key_number_to_key_name(key_signature.key_number).split()[1],
        )
        for key_signature in pm.key_signature_changes
    ]

    time_signatures = [
        TimeSignature(
            time_signature.time,
            time_signature.numerator,
            time_signature.denominator,
        )
        for time_signature in pm.time_signature_changes
    ]

    lyrics = [Lyric(lyric.time, lyric.text) for lyric in pm.lyrics]

    tracks = []
    for track in pm.tracks:
        notes = [
            Note(note.start, note.end, note.pitch, note.velocity)
            for note in track.notes
        ]
        tracks.append(Track(track.program, track.is_drum, track.name, notes))

    return Music(
        meta=MetaData(source=SourceInfo(format="midi")),
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )


def read_midi(
    path: Union[str, Path],
    backend: str = "mido",
    duplicate_note_mode: str = "fifo",
) -> Music:
    """Read a MIDI file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to be read.
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
        Converted MusPy Music object.

    """
    if backend == "mido":
        return read_midi_mido(path, duplicate_note_mode)
    if backend == "pretty_midi":
        return read_midi_pretty_midi(path)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")


def read_midi_pretty_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object using pretty_midi as backend.

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


def read_midi_mido(
    path: Union[str, Path], duplicate_note_mode: str = "fifo"
) -> Music:
    """Read a MIDI file into a Music object using mido as backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to be read.
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
        Converted MusPy Music object.

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

    # Read MIDI file with mido
    midi = MidiFile(filename=str(path))

    # Raise MIDIError if the MIDI file is of Type 2 (i.e., asynchronous)
    if midi.type == 2:
        raise MIDIError("Type 2 MIDI file is not supported.")

    # Raise MIDIError if ticks_per_beat is not positive
    if midi.ticks_per_beat < 1:
        raise MIDIError("`ticks_per_beat` must be positive.")

    time = 0
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
                tempos.append(Tempo(time, tempo2bpm(msg.tempo)))

            # Key signature messages
            elif msg.type == "key_signature":
                if msg.key.endswith("m"):
                    key_signatures.append(
                        KeySignature(time, msg.key[:-1], "minor")
                    )
                else:
                    key_signatures.append(KeySignature(time, msg.key, "major"))

            # Time signature messages
            elif msg.type == "time_signature":
                time_signatures.append(
                    TimeSignature(time, msg.numerator, msg.denominator)
                )

            # Lyric messages
            elif msg.type == "lyrics":
                lyrics.append(Lyric(time, msg.text))

            # Marker messages
            elif msg.type == "marker":
                annotations.append(Annotation(time, msg.text, "marker"))

            # Text messages
            elif msg.type == "text":
                annotations.append(Annotation(time, msg.text, "text"))

            # Copyright messages
            elif msg.type == "copyright":
                copyrights.append(msg.text)

            # === Track specific Data ===

            # Track name messages
            elif msg.type == "track_name":
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
                    track.notes.append(Note(onset, time, msg.note, velocity))
                    del active_notes[note_key][0]

                # 'LIFO': (last in first out) close the latest note on
                elif duplicate_note_mode.lower() == "lifo":
                    onset, velocity = active_notes[note_key][-1]
                    track.notes.append(Note(onset, time, msg.note, velocity))
                    del active_notes[note_key][-1]

                # 'close_all' - close all note on messages
                elif duplicate_note_mode.lower() in ("close_all", "close all"):
                    for onset, velocity in active_notes[note_key]:
                        track.notes.append(
                            Note(onset, time, msg.note, velocity)
                        )
                    del active_notes[note_key]

            # End of track message
            elif msg.type == "end_of_track":
                # Close all active notes
                for (channel, note), note_ons in active_notes.items():
                    program = channel_programs[channel]
                    track = _get_active_track(track_idx, program, channel)
                    for onset, velocity in note_ons:
                        track.notes.append(Note(onset, time, note, velocity))
                break

    music_tracks = []
    for track, track_name in zip(tracks, track_names):
        for sub_track in track.values():
            sub_track.name = track_name
        music_tracks.extend(track.values())

    # Sort notes
    for music_track in music_tracks:
        music_track.notes.sort(
            key=attrgetter("start", "pitch", "end", "velocity")
        )

    # Meta data
    source_info = SourceInfo(
        filename=Path(path).name,
        format="midi",
        copyright=" ".join(copyrights) if copyrights else None,
    )

    return Music(
        resolution=midi.ticks_per_beat,
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=music_tracks,
        meta=MetaData(source=source_info),
    )
