"""MIDI input interface."""
import warnings
from collections import OrderedDict, defaultdict
from operator import attrgetter
from pathlib import Path
from typing import List, Union

import numpy as np
from mido import MidiFile, tempo2bpm
from pretty_midi import Instrument
from pretty_midi import KeySignature as PmKeySignature
from pretty_midi import Lyric as PmLyric
from pretty_midi import Note as PmNote
from pretty_midi import PrettyMIDI
from pretty_midi import TimeSignature as PmTimeSignature

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
from ..music import DEFAULT_RESOLUTION, Music
from ..utils import note_str_to_note_num


class MIDIError(Exception):
    """An error class for MIDI related exceptions."""


def _is_drum(channel):
    # Mido numbers channels 0 to 15 instead of 1 to 16
    return channel == 9


def from_mido(midi: MidiFile, duplicate_note_mode: str = "fifo") -> Music:
    """Return a mido MidiFile object as a Music object.

    Parameters
    ----------
    midi : :class:`mido.MidiFile`
        Mido MidiFile object to convert.
    duplicate_note_mode : {'fifo', 'lifo', 'all'}, default: 'fifo'
        Policy for dealing with duplicate notes. When a note off
        message is presetned while there are multiple correspoding note
        on messages that have not yet been closed, we need a policy to
        decide which note on messages to close.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out): close the latest note on
        - 'all': close all note on messages

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    if duplicate_note_mode.lower() not in ("fifo", "lifo", "all"):
        raise ValueError(
            "`duplicate_note_mode` must be one of 'fifo', 'lifo' and " "'all'."
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
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    lyrics: List[Lyric] = []
    annotations: List[Annotation] = []
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
                tempos.append(
                    Tempo(time=int(time), qpm=float(tempo2bpm(msg.tempo)))
                )

            # Key signature messages
            elif msg.type == "key_signature":
                if msg.key.endswith("m"):
                    mode = "minor"
                    root = note_str_to_note_num(msg.key[:-1])
                else:
                    mode = "major"
                    root = note_str_to_note_num(msg.key)
                key_signatures.append(
                    KeySignature(time=int(time), root=root, mode=mode)
                )

            # Time signature messages
            elif msg.type == "time_signature":
                time_signatures.append(
                    TimeSignature(
                        time=int(time),
                        numerator=int(msg.numerator),
                        denominator=int(msg.denominator),
                    )
                )

            # Lyric messages
            elif msg.type == "lyrics":
                lyrics.append(Lyric(time=int(time), lyric=str(msg.text)))

            # Marker messages
            elif msg.type == "marker":
                annotations.append(
                    Annotation(
                        time=int(time),
                        annotation=str(msg.text),
                        group="marker",
                    )
                )

            # Text messages
            elif msg.type == "text":
                annotations.append(
                    Annotation(
                        time=int(time), annotation=str(msg.text), group="text"
                    )
                )

            # Copyright messages
            elif msg.type == "copyright":
                copyrights.append(str(msg.text))

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
                # Will later be closed by a note off message
                active_notes[(msg.channel, msg.note)].append(
                    (time, msg.velocity)
                )

            # Note off messages
            # NOTE: A note on message with a zero velocity is also
            # considered a note off message
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

                # NOTE: There is no way to disambiguate duplicate notes
                # (of the same pitch on the same channel). Thus, we
                # need a policy for handling duplicate notes.

                # 'FIFO': (first in first out) close the earliest note
                if duplicate_note_mode.lower() == "fifo":
                    onset, velocity = active_notes[note_key][0]
                    track.notes.append(
                        Note(
                            time=int(onset),
                            pitch=int(msg.note),
                            duration=int(time - onset),
                            velocity=int(velocity),
                        )
                    )
                    del active_notes[note_key][0]

                # 'LIFO': (last in first out) close the latest note on
                elif duplicate_note_mode.lower() == "lifo":
                    onset, velocity = active_notes[note_key][-1]
                    track.notes.append(
                        Note(
                            time=int(onset),
                            pitch=int(msg.note),
                            duration=int(time - onset),
                            velocity=int(velocity),
                        )
                    )
                    del active_notes[note_key][-1]

                # 'close_all' - close all note on messages
                elif duplicate_note_mode.lower() == "close_all":
                    for onset, velocity in active_notes[note_key]:
                        track.notes.append(
                            Note(
                                time=int(onset),
                                pitch=int(msg.note),
                                duration=int(time - onset),
                                velocity=int(velocity),
                            )
                        )
                    del active_notes[note_key]

            # Control change messages
            elif msg.type == "control_change":
                # Get the active track
                program = channel_programs[msg.channel]
                track = _get_active_track(track_idx, program, msg.channel)

                # Append the control change message as an annotation
                track.annotations.append(
                    Annotation(
                        time=int(time),
                        annotation={
                            "number": int(msg.control),
                            "value": int(msg.value),
                        },
                        group="control_change",
                    )
                )

            # End of track message
            elif msg.type == "end_of_track":
                break

        # Close all active notes
        for (channel, note), note_ons in active_notes.items():
            program = channel_programs[channel]
            track = _get_active_track(track_idx, program, channel)
            for onset, velocity in note_ons:
                track.notes.append(
                    Note(
                        time=int(onset),
                        pitch=int(note),
                        duration=int(time - onset),
                        velocity=int(velocity),
                    )
                )

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
        title=str(song_title),
        source_format="midi",
        copyright=" ".join(copyrights) if copyrights else None,
    )

    return Music(
        metadata=metadata,
        resolution=int(midi.ticks_per_beat),
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=music_tracks,
    )


def read_midi_mido(
    path: Union[str, Path], duplicate_note_mode: str = "fifo"
) -> Music:
    """Read a MIDI file into a Music object using mido backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to read.
    duplicate_note_mode : {'fifo', 'lifo, 'all'}, default: 'fifo'
        Policy for dealing with duplicate notes. When a note off message
        is presetned while there are multiple correspoding note on
        messages that have not yet been closed, we need a policy to
        decide which note on messages to close.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out):close the latest note on
        - 'all': close all note on messages

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    midi = MidiFile(filename=str(path))
    music = from_mido(midi, duplicate_note_mode=duplicate_note_mode)
    music.metadata.source_filename = Path(path).name
    return music


def from_pretty_midi_key_signature(
    key_signature: PmKeySignature,
) -> KeySignature:
    """Return a pretty_midi KeySignature object as a KeySignature.

    Parameters
    ----------
    key_signature : :class:`pretty_midi.KeySignature`
        pretty_midi KeySignature object to convert.

    Returns
    -------
    :class:`muspy.KeySignature`
        Converted key signature.

    Note
    ----
    The `time` attribute of the converted object will be of type float
    as pretty_midi uses the absolute timing system.

    """
    is_minor, root = divmod(key_signature.key_number, 12)
    mode = "minor" if is_minor else "major"
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return KeySignature(
            time=float(key_signature.time),  # type: ignore
            root=root,
            mode=mode,
        )


def from_pretty_midi_time_signature(
    time_signature: PmTimeSignature,
) -> TimeSignature:
    """Return a pretty_midi TimeSignature object as a TimeSignature.

    Parameters
    ----------
    time_signature : :class:`pretty_midi.TimeSignature`
        pretty_midi TimeSignature object to convert.

    Returns
    -------
    :class:`muspy.TimeSignature`
        Converted time signature.

    Note
    ----
    The `time` attribute of the converted object will be of type float
    as pretty_midi uses the absolute timing system.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return TimeSignature(
            time=float(time_signature.time),  # type: ignore
            numerator=time_signature.numerator,
            denominator=time_signature.denominator,
        )


def from_pretty_midi_lyric(lyric: PmLyric) -> Lyric:
    """Return a pretty_midi Lyric object as a Lyric object.

    Parameters
    ----------
    lyric : :class:`pretty_midi.Lyric`
        pretty_midi Lyric object to convert.

    Returns
    -------
    :class:`muspy.Lyric`
        Converted lyric.

    Note
    ----
    The `time` attribute of the converted object will be of type float
    as pretty_midi uses the absolute timing system.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return Lyric(
            time=float(lyric.time),  # type: ignore
            lyric=str(lyric.text),
        )


def from_pretty_midi_note(note: PmNote) -> Note:
    """Return pretty_midi Note object as a Note object.

    Parameters
    ----------
    note : :class:`pretty_midi.Note`
        pretty_midi Note object to convert.

    Returns
    -------
    :class:`muspy.Note`
        Converted note.

    Note
    ----
    The `time` and `duration` attributes of the converted object will be
    of type float as pretty_midi uses the absolute timing system.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return Note(
            time=float(note.start),  # type: ignore
            duration=float(note.duration),  # type: ignore
            pitch=int(note.pitch),
            velocity=int(note.velocity),
        )


def from_pretty_midi_instrument(instrument: Instrument) -> Track:
    """Return a pretty_midi Instrument object as a Track object.

    Parameters
    ----------
    instrument : :class:`pretty_midi.Instrument`
        pretty_midi Instrument object to convert.

    Returns
    -------
    :class:`muspy.Track`
        Converted track.

    """
    return Track(
        program=int(instrument.program),
        is_drum=bool(instrument.is_drum),
        name=str(instrument.name),
        notes=[from_pretty_midi_note(note) for note in instrument.notes],
    )


def from_pretty_midi(midi: PrettyMIDI, resolution: int = None) -> Music:
    """Return a pretty_midi PrettyMIDI object as a Music object.

    Parameters
    ----------
    midi : :class:`pretty_midi.PrettyMIDI`
        PrettyMIDI object to convert.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    if resolution is None:
        resolution = DEFAULT_RESOLUTION

    tempo_realtimes, tempi = midi.get_tempo_changes()
    assert len(tempi) > 0
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        tempos = [
            Tempo(time=float(time), qpm=float(tempo))  # type: ignore
            for time, tempo in zip(tempo_realtimes, tempi)
        ]

    key_signatures = [
        from_pretty_midi_key_signature(key_signature)
        for key_signature in midi.key_signature_changes
    ]
    time_signatures = [
        from_pretty_midi_time_signature(time_signature)
        for time_signature in midi.time_signature_changes
    ]
    lyrics = [from_pretty_midi_lyric(lyric) for lyric in midi.lyrics]
    tracks = [from_pretty_midi_instrument(track) for track in midi.instruments]
    music = Music(
        metadata=Metadata(source_format="midi"),
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )

    # NOTE: pretty_midi uses the absolute timing system, so we have to
    # convert all the timings into metrical timing.

    # Remove unnecessary tempo changes to speed up the search
    if len(tempi) > 1:
        last_tempo = tempi[0]
        last_time = tempo_realtimes[0]
        tempo_realtimes = tempo_realtimes.tolist()
        tempi = tempi.tolist()
        i = 1
        while i < len(tempo_realtimes):
            if tempi[i] == last_tempo:
                del tempo_realtimes[i]
                del tempi[i]
            elif tempo_realtimes[i] == last_time:
                del tempo_realtimes[i - 1]
                del tempi[i - 1]
            else:
                last_tempo = tempi[i]
                i += 1
        tempo_realtimes = np.array(tempo_realtimes)
        tempi = np.array(tempi)

    if len(tempi) == 1:

        def map_time(time: float) -> int:
            factor = resolution * float(tempi[0]) / 60.0  # type: ignore
            return round(time * factor)

    else:
        # Compute the tempo time in metrical timing of each tempo change
        tempo_times = np.cumsum(
            np.diff(tempo_realtimes) * resolution * tempi[:-1] / 60.0
        )
        tempo_times = np.round(tempo_times).astype(int).tolist()
        tempo_times = np.insert(tempo_times, 0, 0)

        def map_time(time: float) -> int:
            idx = np.searchsorted(tempo_realtimes, time, side="right") - 1
            residual = time - tempo_realtimes[idx]
            factor = resolution * tempi[idx] / 60.0
            return round(tempo_times[idx] + residual * factor)

    # Adjust timing
    music.adjust_time(func=map_time)

    return music


def read_midi_pretty_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object using pretty_midi backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to read.

    Returns
    -------
    :class:`muspy.Music`
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
    backend: {'mido', 'pretty_midi'}, default: 'mido'
        Backend to use.
    duplicate_note_mode : {'fifo', 'lifo, 'all'}, default: 'fifo'
        Policy for dealing with duplicate notes. When a note off message
        is presetned while there are multiple correspoding note on
        messages that have not yet been closed, we need a policy to
        decide which note on messages to close. Only used when `backend`
        is 'mido'.

        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out):close the latest note on
        - 'all': close all note on messages

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    if backend == "mido":
        return read_midi_mido(path, duplicate_note_mode=duplicate_note_mode)
    if backend == "pretty_midi":
        return read_midi_pretty_midi(path)
    raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")
