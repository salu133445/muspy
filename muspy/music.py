"""
Music object
============

This is the core class of MusPy.

"""
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Optional, Union

from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack
from music21.stream import Stream

from .base import ComplexBase
from .classes import (
    Annotation,
    KeySignature,
    Lyric,
    MetaData,
    Tempo,
    TimeSignature,
    Track,
)
from .outputs import save, to_object, to_representation, write
from .visualization import show

__all__ = ["Music"]

DEFAULT_RESOLUTION = 24

# pylint: disable=super-init-not-called


class Music(ComplexBase):
    """A simple yet universal container for symbolic music.

    This is the core class of MusPy, which provides I/O interfaces for common
    formats. A Music object can be constructed in the following ways.

    - :meth:`muspy.Music`: Construct by setting values for attributes.
    - :meth:`muspy.Music.from_dict`: Construct from a dictionary that stores
      the attributes and their values as key-value pairs.
    - :func:`muspy.read`: Read from a MIDI or a MusicXML file.
    - :func:`muspy.load`: Load from a JSON or a YAML file saved by
      :func:`muspy.save` or :class:`muspy.Music.save`.
    - :func:`muspy.from_object`: Convert from a :class:`pretty_midi.PrettyMIDI`
      or :class:`pypianoroll.Multitrack` object.

    Attributes
    ----------
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    tempos : list of :class:`muspy.Tempo`
        Tempo changes.
    key_signatures : list of :class:`muspy.KeySignature` object
        Key signatures changes.
    time_signatures : list of :class:`muspy.TimeSignature` object
        Time signature changes.
    downbeats : list of int or float
        Downbeat positions.
    lyrics : list of :class:`muspy.Lyric`
        Lyrics.
    annotations : list of :class:`muspy.Annotation`
        Annotations.
    tracks : list of :class:`muspy.Track`
        Music tracks.
    meta : :class:`muspy.MetaData` object
        Meta data.

    """

    _attributes = OrderedDict(
        [
            ("resolution", int),
            ("tempos", Tempo),
            ("key_signatures", KeySignature),
            ("time_signatures", TimeSignature),
            ("downbeats", list),
            ("lyrics", Lyric),
            ("annotations", Annotation),
            ("tracks", Track),
            ("meta", MetaData),
        ]
    )
    _optional_attributes = [
        "resolution",
        "tempos",
        "key_signatures",
        "time_signatures",
        "downbeats",
        "lyrics",
        "annotations",
        "tracks",
        "meta",
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
        resolution: Optional[int] = None,
        tempos: Optional[List[Tempo]] = None,
        key_signatures: Optional[List[KeySignature]] = None,
        time_signatures: Optional[List[TimeSignature]] = None,
        downbeats: Optional[List[int]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
        tracks: Optional[List[Track]] = None,
        meta: Optional[MetaData] = None,
    ):
        self.meta = meta if meta is not None else MetaData()
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

    def remove_duplicate_changes(self) -> "Music":
        """Remove duplicate key signature, time signature and tempo changes."""
        tempos = self.tempos
        self.tempos = [
            next_tempo
            for tempo, next_tempo in zip(tempos[:-1], tempos[1:])
            if tempo.tempo != next_tempo.tempo
        ]
        self.tempos.insert(0, tempos[0])

        key_signs = self.key_signatures
        self.key_signatures = [
            next_key_sign
            for key_sign, next_key_sign in zip(key_signs[:-1], key_signs[1:])
            if key_sign.root != next_key_sign.root
            or key_sign.mode != next_key_sign.mode
        ]
        self.key_signatures.insert(0, key_signs[0])

        time_signs = self.time_signatures
        self.time_signatures = [
            next_time_sign
            for time_sign, next_time_sign in zip(
                time_signs[:-1], time_signs[1:]
            )
            if time_sign.numerator != next_time_sign.numerator
            or time_sign.denominator != next_time_sign.denominator
        ]
        self.time_signatures.insert(0, time_signs[0])
        return self

    def get_end_time(
        self, is_sorted: bool = False, realtime: bool = False
    ) -> float:
        """Return the time of the last event in all tracks.

        This includes tempos, key signatures, time signatures, notes offsets,
        lyrics and annotations.

        Parameters
        ----------
        is_sorted : bool
            Whether all the list attributes are sorted. Defaults to False.
        realtime : bool
            Whether to return the end time in real time. Assume 120 quarter per
            minute if no tempo information is available.

        """
        if realtime:
            self.validate("tempos")

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

        if not realtime:
            return end_time

        # If no tempo information is available, assume 120 quarter per minutes
        if not self.tempos:
            return 0.5 * end_time / self.resolution

        # Compute the real time
        position = 0.0
        acc_time = 0.0
        qpm = 120.0
        factor = 60.0 / self.resolution  # type: ignore
        for tempo in self.tempos:
            if tempo.tempo <= 0:
                continue
            acc_time += (tempo.time - position) * factor / qpm
            position = tempo.time
            qpm = tempo.tempo
        acc_time += (end_time - position) * factor / qpm

        return acc_time

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
        return save(self, path, kind, **kwargs)

    def save_json(self, path: Union[str, Path], **kwargs: Any):
        """Save loselessly to a JSON file.

        Refer to :func:`muspy.save_json` for full documentation.

        """
        return save(self, path, "json", **kwargs)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :func:`muspy.save_yaml` for full documentation.

        """
        return save(self, path, "yaml")

    def write(
        self, path: Union[str, Path], kind: Optional[str], **kwargs: Any
    ):
        """Write to a MIDI or a MusicXML file.

        Refer to :func:`muspy.write` for full documentation.

        """
        return write(self, path, kind, **kwargs)

    def write_midi(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MIDI file.

        Refer to :func:`muspy.write_midi` for full documentation.

        """
        return write(self, path, kind="midi", **kwargs)

    def write_musicxml(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MusicXML file.

        Refer to :func:`muspy.write_musicxml` for full documentation.

        """
        return write(self, path, "musicxml", **kwargs)

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

    def to_pianoroll_representation(self, **kwargs: Any) -> ndarray:
        """Return in pianoroll representation.

        Refer to :func:`muspy.to_pianoroll_representation` for full
        documentation.

        """
        return to_representation(self, "pianoroll", **kwargs)

    def to_monotoken_representation(self, **kwargs: Any) -> ndarray:
        """Return in monotoken-based representation.

        Refer to :func:`muspy.to_monotoken_representation` for full
        documentation.

        """
        return to_representation(self, "monotoken", **kwargs)

    def to_polytoken_representation(self, **kwargs: Any) -> ndarray:
        """Return in polytoken-based representation.

        Refer to :func:`muspy.to_polytoken_representation` for full
        documentation.

        """
        return to_representation(self, "polytoken", **kwargs)

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
        return show(self, "pianoroll", **kwargs)
