"""Music class.

This module defines the core class of MusPy---the Music class, a
universal container for symbolic music.

Classes
-------

- Music

Variables
---------

- DEFAULT_RESOLUTION

"""
from collections import OrderedDict
from math import ceil, floor
from pathlib import Path
from typing import Any, Callable, List, TypeVar, Union

import numpy as np
from mido import MidiFile
from music21.stream import Stream
from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .base import ComplexBase
from .classes import (
    Annotation,
    Barline,
    Beat,
    KeySignature,
    Lyric,
    Metadata,
    Tempo,
    TimeSignature,
    Track,
    get_end_time,
)
from .outputs import save, synthesize, to_object, to_representation, write
from .visualization import show

DEFAULT_RESOLUTION = 24
MusicT = TypeVar("MusicT", bound="Music")

__all__ = ["Music", "DEFAULT_RESOLUTION"]

# pylint: disable=super-init-not-called


class Music(ComplexBase):
    """A universal container for symbolic music.

    This is the core class of MusPy. A Music object can be constructed
    in the following ways.

    - :meth:`muspy.Music`: Construct by setting values for attributes
    - :meth:`muspy.Music.from_dict`: Construct from a dictionary that
      stores the attributes and their values as key-value pairs
    - :func:`muspy.read`: Read from a MIDI, a MusicXML or an ABC file
    - :func:`muspy.load`: Load from a JSON or a YAML file saved by
      :func:`muspy.save`
    - :func:`muspy.from_object`: Convert from a `music21.Stream`,
      :class:`mido.MidiFile`, :class:`pretty_midi.PrettyMIDI` or
      :class:`pypianoroll.Multitrack` object

    Attributes
    ----------
    metadata : :class:`muspy.Metadata`, default: `Metadata()`
        Metadata.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    tempos : list of :class:`muspy.Tempo`, default: []
        Tempo changes.
    key_signatures : list of :class:`muspy.KeySignature`, default: []
        Key signatures changes.
    time_signatures : list of :class:`muspy.TimeSignature`, default: []
        Time signature changes.
    barlines : list of :class:`muspy.Barline`, default: []
        Barlines.
    beats : list of :class:`muspy.Beat`, default: []
        Beats.
    lyrics : list of :class:`muspy.Lyric`, default: []
        Lyrics.
    annotations : list of :class:`muspy.Annotation`, default: []
        Annotations.
    tracks : list of :class:`muspy.Track`, default: []
        Music tracks.

    Note
    ----
    Indexing a Music object returns the track of a certain index. That
    is, ``music[idx]`` returns ``music.tracks[idx]``. Length of a Music
    object is the number of tracks. That is, ``len(music)``  returns
    ``len(music.tracks)``.

    """

    _attributes = OrderedDict(
        [
            ("metadata", Metadata),
            ("resolution", int),
            ("tempos", Tempo),
            ("key_signatures", KeySignature),
            ("time_signatures", TimeSignature),
            ("barlines", Barline),
            ("beats", Beat),
            ("lyrics", Lyric),
            ("annotations", Annotation),
            ("tracks", Track),
        ]
    )
    _optional_attributes = [
        "metadata",
        "resolution",
        "tempos",
        "key_signatures",
        "time_signatures",
        "barlines",
        "beats",
        "lyrics",
        "annotations",
        "tracks",
    ]
    _list_attributes = [
        "tempos",
        "key_signatures",
        "time_signatures",
        "barlines",
        "beats",
        "lyrics",
        "annotations",
        "tracks",
    ]

    def __init__(
        self,
        metadata: Metadata = None,
        resolution: int = None,
        tempos: List[Tempo] = None,
        key_signatures: List[KeySignature] = None,
        time_signatures: List[TimeSignature] = None,
        barlines: List[Barline] = None,
        beats: List[Beat] = None,
        lyrics: List[Lyric] = None,
        annotations: List[Annotation] = None,
        tracks: List[Track] = None,
    ):
        self.metadata = metadata if metadata is not None else Metadata()
        self.resolution = (
            resolution if resolution is not None else DEFAULT_RESOLUTION
        )
        self.tempos = tempos if tempos is not None else []
        self.key_signatures = (
            key_signatures if key_signatures is not None else []
        )
        self.time_signatures = (
            time_signatures if time_signatures is not None else []
        )
        self.beats = beats if beats is not None else []
        self.barlines = barlines if barlines is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []
        self.tracks = tracks if tracks is not None else []

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, key: int) -> Track:
        return self.tracks[key]

    def __setitem__(self, key: int, value: Track):
        self.tracks[key] = value

    def __delitem__(self, key: int):
        del self.tracks[key]

    def get_end_time(self, is_sorted: bool = False) -> int:
        """Return the time of the last event across all the tracks.

        This includes tempos, key signatures, time signatures, barlines,
        beats, lyrics, annotations, note offsets and chord offsets.

        Parameters
        ----------
        is_sorted : bool, default: False
            Whether all the list attributes are sorted.

        """
        if self.tracks:
            track_end_time = max(
                track.get_end_time(is_sorted) for track in self.tracks
            )
        else:
            track_end_time = 0

        end_time = max(
            get_end_time(self.tempos, is_sorted),
            get_end_time(self.key_signatures, is_sorted),
            get_end_time(self.time_signatures, is_sorted),
            get_end_time(self.barlines, is_sorted),
            get_end_time(self.beats, is_sorted),
            get_end_time(self.lyrics, is_sorted),
            get_end_time(self.annotations, is_sorted),
            track_end_time,
        )

        return end_time

    def get_real_end_time(self, is_sorted: bool = False) -> float:
        """Return the end time in realtime.

        This includes tempos, key signatures, time signatures, note
        offsets, lyrics and annotations. Assume 120 qpm (quarter notes
        per minute) if no tempo information is available.

        Parameters
        ----------
        is_sorted : bool, default: False
            Whether all the list attributes are sorted.

        """
        # Get symbolic end time
        end_time = self.get_end_time(is_sorted=is_sorted)

        # If no tempo information is available, assume 120 qpm
        if not self.tempos:
            return 0.5 * end_time / self.resolution

        # Compute the real end time
        position = 0.0
        qpm = 120.0
        factor = 60.0 / self.resolution
        real_end_time = 0.0
        for tempo in self.tempos:
            real_end_time += (tempo.time - position) * factor / qpm
            position = tempo.time
            qpm = tempo.qpm
        real_end_time += (end_time - position) * factor / qpm

        return real_end_time

    def infer_barlines(self: MusicT, overwrite: bool = False) -> MusicT:
        """Infer barlines from the time signatures.

        This assumes that there is a barline at each time signature
        change.

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing barlines.

        Returns
        -------
        Object itself.

        Raises
        ------
        ValueError
            If no time signature is found.

        """
        if not overwrite and self.beats:
            return self
        if not self.time_signatures:
            raise ValueError(
                "Cannot infer barlines as no time signature is found."
            )
        self.barlines = []
        for i, time_sign in enumerate(self.time_signatures):
            if i == len(self.time_signatures) - 1:
                end = self.get_end_time()
            else:
                end = self.time_signatures[i + 1].time
            # NOTE: `resolution`` denotes the number of time steps per
            # quarter note
            bar_length = (4 * self.resolution) * (
                time_sign.numerator / time_sign.denominator
            )
            for time in np.arange(time_sign.time, end, bar_length):
                self.barlines.append(Barline(time=int(round(time))))
        return self

    def infer_barlines_and_beats(
        self: MusicT, overwrite: bool = False
    ) -> MusicT:
        """Infer barlines and beats from the time signature changes.

        This assumes that there is a downbeat at each time signature
        change (this is not always true, e.g., for a pickup measure).
        Return an empty list if no time signature is found.

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing barlines or beats.

        Returns
        -------
        Object itself.

        Raises
        ------
        ValueError
            If no time signature is found.

        """
        if not overwrite and (self.barlines or self.beats):
            return self
        if not self.time_signatures:
            raise ValueError(
                "Cannot infer barlines and beats as no time signature is "
                "found."
            )
        self.barlines = []
        self.beats = []
        for i, time_sign in enumerate(self.time_signatures):
            if i == len(self.time_signatures) - 1:
                end = self.get_end_time()
            else:
                end = self.time_signatures[i + 1].time
            # NOTE: `resolution`` denotes the number of time steps per
            # quarter note
            bar_length = (4 * self.resolution) * (
                time_sign.numerator / time_sign.denominator
            )
            for time in np.arange(time_sign.time, end, bar_length):
                self.barlines.append(Barline(time=int(round(time))))
            beat_length = 4 * self.resolution / time_sign.denominator
            for time in np.arange(time_sign.time, end, beat_length):
                self.beats.append(Beat(time=int(round(time))))
        return self

    def adjust_resolution(
        self: MusicT,
        target: int = None,
        factor: float = None,
        rounding: Union[str, Callable] = "round",
    ) -> MusicT:
        """Adjust resolution and timing of all time-stamped objects.

        Parameters
        ----------
        target : int, optional
            Target resolution.
        factor : int or float, optional
            Factor used to adjust the resolution based on the formula:
            `new_resolution = old_resolution * factor`. For example, a
            factor of 2 double the resolution, and a factor of 0.5 halve
            the resolution.
        rounding : {'round', 'ceil', 'floor'} or callable, default:
        'round'
            Rounding mode.

        Returns
        -------
        Object itself.

        """
        if self.resolution is None:
            raise TypeError("`resolution` must be given.")
        if self.resolution < 0:
            raise ValueError("`resolution` must be positive.")

        if target is None and factor is None:
            raise ValueError("One of `target` and `factor` must be given.")
        if target is not None and factor is not None:
            raise ValueError("Only one of `target` and `factor` can be given.")

        if target is None and self.resolution == target:
            return self

        if rounding is None or rounding == "round":
            rounding = round
        elif rounding == "ceil":
            rounding = ceil
        elif rounding == "floor":
            rounding = floor
        elif isinstance(rounding, str):
            raise ValueError(f"Unrecognized rounding mode : {rounding} .")

        if target is not None:
            if not isinstance(target, int):
                raise TypeError("`target` must be an integer.")
            target_ = int(target)
            factor_ = target / self.resolution

        if factor is not None:
            new_resolution = float(self.resolution * factor)
            if not new_resolution.is_integer():
                raise ValueError(
                    f"`factor` must be a factor of the original resolution "
                    f"{self.resolution}, but got : {factor}."
                )
            factor_ = float(factor)
            target_ = int(new_resolution)

        self.resolution = int(target_)
        self.adjust_time(lambda time: rounding(time * factor_))  # type: ignore
        return self

    def clip(self: MusicT, lower: int = 0, upper: int = 127) -> MusicT:
        """Clip the velocity of each note for each track.

        Parameters
        ----------
        lower : int, default: 0
            Lower bound.
        upper : int, default: 127
            Upper bound.

        Returns
        -------
        Object itself.

        """
        for track in self.tracks:
            track.clip(lower, upper)
        return self

    def transpose(self: MusicT, semitone: int) -> MusicT:
        """Transpose all the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the
            pitches.

        Returns
        -------
        Object itself.

        Notes
        -----
        Drum tracks are skipped.

        """
        for track in self.tracks:
            if not track.is_drum:
                track.transpose(semitone)
        return self

    def trim(self: MusicT, end: int) -> MusicT:
        """Trim the track.

        Parameters
        ----------
        end : int
            End time, excluding (i.e, the max time will be `end` - 1).

        Returns
        -------
        Object itself.

        """
        self.tempos = [x for x in self.tempos if x.time < end]
        self.key_signatures = [x for x in self.key_signatures if x.time < end]
        self.time_signatures = [
            x for x in self.time_signatures if x.time < end
        ]
        self.barlines = [x for x in self.barlines if x.time < end]
        self.beats = [x for x in self.beats if x.time < end]
        self.lyrics = [x for x in self.lyrics if x.time < end]
        self.annotations = [x for x in self.annotations if x.time < end]
        for track in self.tracks:
            track.trim(end)
        return self

    def save(self, path: Union[str, Path], kind: str = None, **kwargs: Any):
        """Save loselessly to a JSON or a YAML file.

        Refer to :func:`muspy.save` for full documentation.

        """
        return save(path, self, kind=kind, **kwargs)

    def save_json(self, path: Union[str, Path], **kwargs: Any):
        """Save loselessly to a JSON file.

        Refer to :func:`muspy.save_json` for full documentation.

        """
        return save(path, self, kind="json", **kwargs)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :func:`muspy.save_yaml` for full documentation.

        """
        return save(path, self, kind="yaml")

    def write(self, path: Union[str, Path], kind: str = None, **kwargs: Any):
        """Write to a MIDI, a MusicXML, an ABC or an audio file.

        Refer to :func:`muspy.write` for full documentation.

        """
        return write(path, self, kind=kind, **kwargs)

    def write_midi(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MIDI file.

        Refer to :func:`muspy.write_midi` for full documentation.

        """
        return write(path, self, kind="midi", **kwargs)

    def write_musicxml(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MusicXML file.

        Refer to :func:`muspy.write_musicxml` for full documentation.

        """
        return write(path, self, kind="musicxml", **kwargs)

    def write_abc(self, path: Union[str, Path], **kwargs: Any):
        """Write to an ABC file.

        Refer to :func:`muspy.write_abc` for full documentation.

        """
        return write(path, self, kind="abc", **kwargs)

    def write_audio(self, path: Union[str, Path], **kwargs: Any):
        """Write to an audio file.

        Refer to :func:`muspy.write_audio` for full documentation.

        """
        return write(path, self, kind="audio", **kwargs)

    def to_object(self, kind: str, **kwargs: Any):
        """Return as an object in other libraries.

        Refer to :func:`muspy.to_object` for full documentation.

        """
        return to_object(self, kind=kind, **kwargs)

    def to_music21(self, **kwargs: Any) -> Stream:
        """Return as a Stream object.

        Refer to :func:`muspy.to_music21` for full documentation.

        """
        return to_object(self, kind="music21", **kwargs)

    def to_mido(self, **kwargs: Any) -> MidiFile:
        """Return as a MidiFile object.

        Refer to :func:`muspy.to_mido` for full documentation.

        """
        return to_object(self, kind="mido", **kwargs)

    def to_pretty_midi(self, **kwargs: Any) -> PrettyMIDI:
        """Return as a PrettyMIDI object.

        Refer to :func:`muspy.to_pretty_midi` for full documentation.

        """
        return to_object(self, kind="pretty_midi", **kwargs)

    def to_pypianoroll(self, **kwargs: Any) -> Multitrack:
        """Return as a Multitrack object.

        Refer to :func:`muspy.to_pypianoroll` for full documentation.

        """
        return to_object(self, kind="pypianoroll", **kwargs)

    def to_representation(self, kind: str, **kwargs: Any) -> ndarray:
        """Return in a specific representation.

        Refer to :func:`muspy.to_representation` for full documentation.

        """
        return to_representation(self, kind=kind, **kwargs)

    def to_pitch_representation(self, **kwargs: Any) -> ndarray:
        """Return in pitch-based representation.

        Refer to :func:`muspy.to_pitch_representation` for full
        documentation.

        """
        return to_representation(self, kind="pitch", **kwargs)

    def to_pianoroll_representation(self, **kwargs: Any) -> ndarray:
        """Return in piano-roll representation.

        Refer to :func:`muspy.to_pianoroll_representation` for full
        documentation.

        """
        return to_representation(self, kind="piano-roll", **kwargs)

    def to_event_representation(self, **kwargs: Any) -> ndarray:
        """Return in event-based representation.

        Refer to :func:`muspy.to_event_representation` for full
        documentation.

        """
        return to_representation(self, kind="event", **kwargs)

    def to_note_representation(self, **kwargs: Any) -> ndarray:
        """Return in note-based representation.

        Refer to :func:`muspy.to_note_representation` for full
        documentation.

        """
        return to_representation(self, kind="note", **kwargs)

    def show(self, kind: str, **kwargs: Any):
        """Show visualization.

        Refer to :func:`muspy.show` for full documentation.

        """
        return show(self, kind, **kwargs)

    def show_score(self, **kwargs: Any):
        """Show score visualization.

        Refer to :func:`muspy.show_score` for full documentation.

        """
        return show(self, kind="score", **kwargs)

    def show_pianoroll(self, **kwargs: Any):
        """Show pianoroll visualization.

        Refer to :func:`muspy.show_pianoroll` for full documentation.

        """
        return show(self, kind="piano-roll", **kwargs)

    def synthesize(self, **kwargs) -> ndarray:
        """Synthesize a Music object to raw audio.

        Refer to :func:`muspy.synthesize` for full documentation.

        """
        return synthesize(self, **kwargs)
