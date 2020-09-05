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
from pathlib import Path
from typing import Any, List, Optional, Union

from music21.stream import Stream
from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .base import ComplexBase
from .classes import (
    Annotation,
    KeySignature,
    Lyric,
    Metadata,
    Tempo,
    TimeSignature,
    Track,
)
from .outputs import save, synthesize, to_object, to_representation, write
from .visualization import show

__all__ = ["Music", "DEFAULT_RESOLUTION"]

DEFAULT_RESOLUTION = 24

# pylint: disable=super-init-not-called


class Music(ComplexBase):
    """A universal container for symbolic music.

    This is the core class of MusPy. A Music object can be constructed in
    the following ways.

    - :meth:`muspy.Music`: Construct by setting values for attributes.
    - :meth:`muspy.Music.from_dict`: Construct from a dictionary that stores
      the attributes and their values as key-value pairs.
    - :func:`muspy.read`: Read from a MIDI, a MusicXML or an ABC file.
    - :func:`muspy.load`: Load from a JSON or a YAML file saved by
      :func:`muspy.save`.
    - :func:`muspy.from_object`: Convert from a `music21.Stream`, a
      :class:`mido.MidiFile`, a :class:`pretty_midi.PrettyMIDI` or a
      :class:`pypianoroll.Multitrack` object.

    Attributes
    ----------
    metadata : :class:`muspy.Metadata` object
        Metadata.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    tempos : list of :class:`muspy.Tempo`
        Tempo changes.
    key_signatures : list of :class:`muspy.KeySignature` object
        Key signatures changes.
    time_signatures : list of :class:`muspy.TimeSignature` object
        Time signature changes.
    downbeats : list of int
        Downbeat positions.
    lyrics : list of :class:`muspy.Lyric`
        Lyrics.
    annotations : list of :class:`muspy.Annotation`
        Annotations.
    tracks : list of :class:`muspy.Track`
        Music tracks.

    Tip
    ---
    Indexing a Music object gives the track of a certain index. That is,
    `music[idx]` is equivalent to `music.tracks[idx]`. Length of a Music
    object is the number of tracks. That is, `len(music)`  is equivalent to
    `len(music.tracks)`.

    """

    _attributes = OrderedDict(
        [
            ("metadata", Metadata),
            ("resolution", int),
            ("tempos", Tempo),
            ("key_signatures", KeySignature),
            ("time_signatures", TimeSignature),
            ("downbeats", int),
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
        "downbeats",
        "lyrics",
        "annotations",
        "tracks",
    ]
    _temporal_attributes = ["downbeats"]
    _list_attributes = [
        "tempos",
        "key_signatures",
        "time_signatures",
        "downbeats",
        "lyrics",
        "annotations",
        "tracks",
    ]

    def __init__(
        self,
        metadata: Optional[Metadata] = None,
        resolution: Optional[int] = None,
        tempos: Optional[List[Tempo]] = None,
        key_signatures: Optional[List[KeySignature]] = None,
        time_signatures: Optional[List[TimeSignature]] = None,
        downbeats: Optional[List[int]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
        tracks: Optional[List[Track]] = None,
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
        self.downbeats = downbeats if downbeats is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []
        self.tracks = tracks if tracks is not None else []

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, key: int) -> Track:
        return self.tracks[key]

    def __setitem__(self, key: int, value: Track):
        self.tracks[key] = value

    def get_end_time(self, is_sorted: bool = False) -> int:
        """Return the end time, i.e., the time of the last event in all tracks.

        This includes tempos, key signatures, time signatures, notes offsets,
        lyrics and annotations.

        Parameters
        ----------
        is_sorted : bool
            Whether all the list attributes are sorted. Defaults to False.

        """

        def _get_end_time(list_):
            if not list_:
                return 0
            if is_sorted:
                return list_[-1].time
            return max(item.time for item in list_)

        if self.tracks:
            track_end_time = max(
                track.get_end_time(is_sorted) for track in self.tracks
            )
        else:
            track_end_time = 0

        end_time = max(
            _get_end_time(self.tempos),
            _get_end_time(self.key_signatures),
            _get_end_time(self.time_signatures),
            _get_end_time(self.lyrics),
            _get_end_time(self.annotations),
            track_end_time,
        )

        return end_time

    def get_real_end_time(self, is_sorted: bool = False) -> float:
        """Return the end time in realtime.

        This includes tempos, key signatures, time signatures, notes offsets,
        lyrics and annotations. Assume 120 qpm (quarter notes per minute) if no
        tempo information is available.

        Parameters
        ----------
        is_sorted : bool
            Whether all the list attributes are sorted. Defaults to False.

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

    def adjust_resolution(
        self, target: Optional[int] = None, factor: Optional[float] = None
    ) -> "Music":
        """Adjust resolution and update the timing of time-stamped objects.

        Parameters
        ----------
        target : int, optional
            Target resolution.
        factor : int or float, optional
            Factor used to adjust the resolution based on the formula:
            `new_resolution = old_resolution * factor`. For example, a factor
            of 2 double the resolution, and a factor of 0.5 halve the
            resolution.

        Returns
        -------
        Object itself.

        """
        if self.resolution is None:
            raise TypeError("`resolution` must not be None.")
        if self.resolution < 0:
            raise ValueError("`resolution` must be positive.")

        if target is None and factor is None:
            raise ValueError("`target` and `factor` must not be both None.")
        if target is not None and factor is not None:
            raise ValueError("Either `target` or `factor` must be given.")

        if target is not None:
            if not isinstance(target, int):
                raise TypeError("`target` must be an integer.")
            target_ = int(target)
            factor_ = target / self.resolution

        if factor is not None:
            new_resolution = self.resolution * factor
            if not new_resolution.is_integer():
                raise ValueError(
                    "`factor` must be a factor of the resolution."
                )
            factor_ = float(factor)
            target_ = int(new_resolution)

        self.resolution = int(target_)
        self.adjust_time(lambda time: round(time * factor_))
        return self

    def clip(self, lower: int = 0, upper: int = 127) -> "Music":
        """Clip the velocity of each note for each track.

        Parameters
        ----------
        lower : int, optional
            Lower bound. Defaults to 0.
        upper : int, optional
            Upper bound. Defaults to 127.

        Returns
        -------
        Object itself.

        """
        for track in self.tracks:
            track.clip(lower, upper)
        return self

    def transpose(self, semitone: int) -> "Music":
        """Transpose all the notes for all tracks by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value raises
            the pitches, while a negative value lowers the pitches.

        Returns
        -------
        Object itself.

        """
        for track in self.tracks:
            track.transpose(semitone)
        return self

    def save(
        self, path: Union[str, Path], kind: Optional[str] = None, **kwargs: Any
    ):
        """Save loselessly to a JSON or a YAML file.

        Refer to :func:`muspy.save` for full documentation.

        """
        return save(path, self, kind, **kwargs)

    def save_json(self, path: Union[str, Path], **kwargs: Any):
        """Save loselessly to a JSON file.

        Refer to :func:`muspy.save_json` for full documentation.

        """
        return save(path, self, "json", **kwargs)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :func:`muspy.save_yaml` for full documentation.

        """
        return save(path, self, "yaml")

    def write(
        self, path: Union[str, Path], kind: Optional[str] = None, **kwargs: Any
    ):
        """Write to a MIDI, a MusicXML, an ABC or an audio file.

        Refer to :func:`muspy.write` for full documentation.

        """
        return write(path, self, kind, **kwargs)

    def write_midi(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MIDI file.

        Refer to :func:`muspy.write_midi` for full documentation.

        """
        return write(path, self, kind="midi", **kwargs)

    def write_musicxml(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MusicXML file.

        Refer to :func:`muspy.write_musicxml` for full documentation.

        """
        return write(path, self, "musicxml", **kwargs)

    def write_abc(self, path: Union[str, Path], **kwargs: Any):
        """Write to an ABC file.

        Refer to :func:`muspy.write_abc` for full documentation.

        """
        return write(path, self, "abc", **kwargs)

    def write_audio(self, path: Union[str, Path], **kwargs: Any):
        """Write to an audio file.

        Refer to :func:`muspy.write_audio` for full documentation.

        """
        return write(path, self, "audio", **kwargs)

    def to_object(self, target: str, **kwargs: Any):
        """Convert to a target class.

        Refer to :func:`muspy.to_object` for full documentation.

        """
        return to_object(self, target, **kwargs)

    def to_music21(self, **kwargs: Any) -> Stream:
        """Return as a Stream object.

        Refer to :func:`muspy.to_music21` for full documentation.

        """
        return to_object(self, "music21", **kwargs)

    def to_pretty_midi(self, **kwargs: Any) -> PrettyMIDI:
        """Return as a PrettyMIDI object.

        Refer to :func:`muspy.to_pretty_midi` for full documentation.

        """
        return to_object(self, "pretty_midi", **kwargs)

    def to_pypianoroll(self, **kwargs: Any) -> Multitrack:
        """Return as a Multitrack object.

        Refer to :func:`muspy.to_pypianoroll` for full documentation.

        """
        return to_object(self, "pypianoroll", **kwargs)

    def to_representation(self, kind: str, **kwargs: Any) -> ndarray:
        """Return in a specific representation.

        Refer to :func:`muspy.to_representation` for full documentation.

        """
        return to_representation(self, kind, **kwargs)

    def to_pitch_representation(self, **kwargs: Any) -> ndarray:
        """Return in pitch-based representation.

        Refer to :func:`muspy.to_pitch_representation` for full
        documentation.

        """
        return to_representation(self, "pitch", **kwargs)

    def to_pianoroll_representation(self, **kwargs: Any) -> ndarray:
        """Return in piano-roll representation.

        Refer to :func:`muspy.to_pianoroll_representation` for full
        documentation.

        """
        return to_representation(self, "piano-roll", **kwargs)

    def to_event_representation(self, **kwargs: Any) -> ndarray:
        """Return in event-based representation.

        Refer to :func:`muspy.to_event_representation` for full documentation.

        """
        return to_representation(self, "event", **kwargs)

    def to_note_representation(self, **kwargs: Any) -> ndarray:
        """Return in note-based representation.

        Refer to :func:`muspy.to_note_representation` for full documentation.

        """
        return to_representation(self, "note", **kwargs)

    def show(self, kind: str, **kwargs: Any):
        """Show visualization.

        Refer to :func:`muspy.show` for full documentation.

        """
        return show(self, kind, **kwargs)

    def show_score(self, **kwargs: Any):
        """Show score visualization.

        Refer to :func:`muspy.show_score` for full documentation.

        """
        return show(self, "score", **kwargs)

    def show_pianoroll(self, **kwargs: Any):
        """Show pianoroll visualization.

        Refer to :func:`muspy.show_pianoroll` for full documentation.

        """
        return show(self, "piano-roll", **kwargs)

    def synthesize(self, **kwargs) -> ndarray:
        """Synthesize a Music object to raw audio.

        Refer to :func:`muspy.synthesize` for full documentation.

        """
        return synthesize(self, **kwargs)
