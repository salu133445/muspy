"""
Core classes
============

These are the core classes of MusPy. All these objects inherit from
the base class :class:`muspy.Base`.

"""
from collections import OrderedDict
from typing import Any, List, Optional

from .base import Base, ComplexBase
from .schemas import DEFAULT_SCHEMA_VERSION

DEFAULT_RESOLUTION = 24

__all__ = [
    "Annotation",
    "KeySignature",
    "Lyric",
    "MetaData",
    "Note",
    "SongInfo",
    "SourceInfo",
    "Tempo",
    "TimeSignature",
    "Timing",
    "Track",
]

# pylint: disable=super-init-not-called


class SongInfo(Base):
    """A container for song information.

    Attributes
    ----------
    title : str, optional
        Song title.
    artist : str, optional
        Main artist of the song.
    creators : list of str, optional
        Creator(s) of the song. Defaults to an empty list.

    """

    _attributes = OrderedDict(
        [("title", str), ("artist", str), ("creators", str)]
    )
    _optional_attributes = ["title", "artist"]

    def __init__(
        self,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        creators: Optional[List[str]] = None,
    ):
        self.title = title
        self.artist = artist
        self.creators = creators if creators is not None else []


class SourceInfo(Base):
    """A container for source information.

    Attributes
    ----------
    collection : str, optional
        Name of the collection.
    filename : str, optional
        Relative path to the source file with respect to the collection
        root.
    format : {'midi', 'musicxml'}, optional
        Format of the source file.
    id : str, optional
        Unique ID of the file.

    """

    _attributes = OrderedDict(
        [("collection", str), ("filename", str), ("format", str), ("id", str)]
    )
    _optional_attributes = ["collection", "filename", "format", "id"]

    def __init__(
        self,
        collection: Optional[str] = None,
        filename: Optional[str] = None,
        format: Optional[str] = None,
        id: Optional[str] = None,
    ):
        # pylint: disable=redefined-builtin
        self.collection = collection
        self.filename = filename
        self.format = format
        self.id = id


class MetaData(Base):
    """A container for meta data.

    Attributes
    ----------
    schema_version : str
        Schema version.
    song : :class:`muspy.SongInfo` object, optional
        Song infomation.
    source : :class:`muspy.SourceInfo` object, optional
        Source infomation.

    """

    _attributes = OrderedDict(
        [("schema_version", str), ("song", SongInfo), ("source", SourceInfo)]
    )
    _optional_attributes = ["song", "source"]

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        song: Optional[SongInfo] = None,
        source: Optional[SourceInfo] = None,
    ):
        self.schema_version = schema_version
        self.song = song
        self.source = source

    def validate(self, attr=None):
        """Raise proper errors if a certain attribute is invalid.

        When `attr` is not given, check all attributes.

        """
        if self.schema_version is None:
            raise TypeError("`schema_version` must not be None.")
        self._validate()


class Tempo(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int or float
        Start time of the tempo, in time steps or seconds.
    tempo : float
        Tempo in bpm (beats per minute).

    """

    _attributes = OrderedDict(
        [("time", (int, float)), ("tempo", (int, float))]
    )
    _temporal_attributes = ["time"]

    def __init__(self, time: float, tempo: float):
        self.time = time
        self.tempo = tempo


class Timing(ComplexBase):
    """A container for song information.

    Attributes
    ----------
    is_metrical : bool, optional
        If true, the timing is in time steps, otherwise in seconds.
        Defaults to True
    resolution : int, optional
        Time steps per beat (only effective when `is_metrical` is true).
        Defaults to `muspy.DEFAULT_RESOLUTION`.
    tempos : list of :class:`muspy.Tempo`
        Tempo changes. Defaults to an empty list.

    """

    _attributes = OrderedDict(
        [("is_metrical", bool), ("resolution", int), ("tempos", Tempo)]
    )
    _optional_attributes = ["resolution"]
    _list_attributes = ["tempos"]

    def __init__(
        self,
        is_metrical: bool = True,
        resolution: Optional[int] = None,
        tempos: Optional[List[Tempo]] = None,
    ):
        self.is_metrical = is_metrical
        self.resolution = (
            DEFAULT_RESOLUTION
            if is_metrical and resolution is None
            else resolution
        )
        self.tempos = tempos if tempos is not None else []

    def validate(self, attr=None):
        """Raise proper errors if any attribute is invalid."""
        if attr in ("is_metrical", None):
            self._validate_type("is_metrical")
        if self.is_metrical:
            if attr in ("resolution", None):
                self._validate_type("resolution")
                if self.resolution < 1:
                    raise ValueError("`resolution` must be positive.")
            if attr in ("tempos", None):
                self._validate("tempos")

    def remove_duplicate_changes(self):
        """Remove duplicate tempo changes."""
        tempos = self.tempos
        self.tempos = [
            next_tempo
            for tempo, next_tempo in zip(tempos[:-1], tempos[1:])
            if tempo.tempo != next_tempo.tempo
        ]
        self.tempos.insert(0, tempos[0])
        return self

    def get_end_time(self, is_sorted: bool = False) -> float:
        """Return the time of the last tempo event.

        Parameters
        ----------
        is_sorted : bool
            Whether the tempos are sorted. Defaults to False.

        """
        if not self.tempos:
            return 0
        if is_sorted:
            return self.tempos[-1].time
        return max(item.time for item in self.tempos)


class KeySignature(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int or float
        Start time of the key signature, in time steps or seconds.
    root : str
        Root of the key signature.
    mode : str
        Mode of the key signature.

    """

    _attributes = OrderedDict(
        [("time", (int, float)), ("root", str), ("mode", str)]
    )
    _temporal_attributes = ["time"]

    def __init__(self, time: float, root: str, mode: str):
        self.time = time
        self.root = root
        self.mode = mode


class TimeSignature(Base):
    """A container for time signature.

    Attributes
    ----------
    time : int or float
        Start time of the time signature, in time steps or seconds.
    numerator : int
        Numerator of the time signature.
    denominator : int
        Denominator of the time signature.

    """

    _attributes = OrderedDict(
        [("time", (int, float)), ("numerator", str), ("denominator", str)]
    )
    _temporal_attributes = ["time"]

    def __init__(self, time: float, numerator: int, denominator: int):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

    def validate(self):
        """Raise proper errors if any attribute is invalid."""
        self._validate()
        if self.numerator < 1:
            raise ValueError("`numerator` must be positive.")
        if self.denominator < 1:
            raise ValueError("`denominator` must be positive.")


class Lyric(Base):
    """A container for lyric.

    Attributes
    ----------
    time : int or float
        Start time of the lyric, in time steps or seconds.
    lyric : str
        Lyric (sentence, word, syllable, etc.).

    """

    _attributes = OrderedDict([("time", (int, float)), ("lyric", str)])
    _temporal_attributes = ["time"]

    def __init__(self, time: float, lyric: str):
        self.time = time
        self.lyric = lyric


class Annotation(Base):
    """A container for annotation.

    Attributes
    ----------
    time : int or float
        Start time of the annotation, in time steps or seconds.
    annotation : any object
        Annotation of any type.
    group : str, optional
        Group name for better organizing the annotations.

    """

    _attributes = _attributes = OrderedDict(
        [("time", (int, float)), ("annotation", str)]
    )
    _temporal_attributes = ["time"]

    def __init__(
        self, time: float, annotation: Any, group: Optional[str] = None
    ):
        self.time = time
        self.annotation = annotation
        self.group = group


class Note(Base):
    """A container for note.

    Attributes
    ----------
    start : int or float
        Start time of the note, in time steps or seconds.
    end : int or float
        End time of the note, in time steps or seconds.
    pitch : int
        Note pitch, as a MIDI note number.
    velocity : int
        Note velocity.

    """

    _attributes = OrderedDict(
        [
            ("start", (int, float)),
            ("end", (int, float)),
            ("pitch", int),
            ("velocity", (int, float)),
        ]
    )
    _temporal_attributes = ["start", "end"]

    def __init__(
        self, start: float, end: float, pitch: int, velocity: float,
    ):
        self.start = start
        self.end = end
        self.pitch = pitch
        self.velocity = velocity

    @property
    def duration(self):
        """Duration of the note."""
        return self.end - self.start

    @duration.setter
    def duration(self, duration):
        """Setter for duration."""
        self.end = self.start + duration

    def validate(self):
        """Raise proper errors if any attribute is invalid."""
        self._validate()
        if self.start < 0:
            raise ValueError("`start` must be nonnegative.")
        if self.end < self.start:
            raise ValueError("`end` must be greater than `start`.")
        if 0 <= self.pitch < 128:
            raise ValueError("`pitch` must be in between 0 to 127.")
        if 0 <= self.velocity < 128:
            raise ValueError("`velocity` must be in between 0 to 127.")

    def transpose(self, semitone: int):
        """Transpose the note by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the note. A positive value
            raises the pitch, while a negative value lowers the pitch.

        """
        self.pitch += semitone
        return self

    def clip(self, lower: float = 0, upper: float = 127):
        """Clip the velocity of the note.

        Parameters
        ----------
        lower : int or float, optional
            Lower bound. Defaults to 0.
        upper : int or float, optional
            Upper bound. Defaults to 127.

        """
        assert upper >= lower, "`upper` must be greater than `lower`."
        if self.velocity > upper:
            self.velocity = upper
        elif self.velocity < lower:
            self.velocity = lower
        return self


class Chord(ComplexBase):
    """A container for chord.

    Attributes
    ----------
    start : int or float
        Start time of the note, in time steps or seconds.
    end : int or float
        End time of the note, in time steps or seconds.
    pitches : list of int
        Note pitches, as MIDI note numbers.

    """

    _attributes = OrderedDict(
        [("start", (int, float)), ("end", (int, float)), ("pitches", int)]
    )
    _temporal_attributes = ["start", "end"]
    _list_attributes = ["pitches"]

    def __init__(self, start: float, end: float, pitches: List[int]):
        self.start = start
        self.end = end
        self.pitches = pitches

    @property
    def duration(self):
        """Duration of the note."""
        return self.end - self.start

    @duration.setter
    def duration(self, duration):
        """Setter for duration."""
        self.end = self.start + duration

    def validate(self):
        """Raise proper errors if any attribute is invalid."""
        self._validate()
        if self.start < 0:
            raise ValueError("`start` must be nonnegative.")
        if self.end < self.start:
            raise ValueError("`end` must be greater than `start`.")
        for pitch in self.pitches:
            if 0 <= pitch < 128:
                raise ValueError("`pitch` must be in between 0 to 127.")

    def transpose(self, semitone: int):
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the note. A positive value
            raises the pitch, while a negative value lowers the pitch.

        """
        self.pitches += [pitch + semitone for pitch in self.pitches]
        return self


class Track(ComplexBase):
    """A container for music track.

    Attributes
    ----------
    program : int, optional
        Program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand
        Piano).
    is_drum : bool, optional
        A boolean indicating if it is a percussion track. Defaults to
        False.
    name : str, optional
        Track name.
    notes : list of :class:`muspy.Note` objects, optional
        Musical notes. Defaults to an empty list.
    chords : list of :class:`muspy.Chord` objects, optional
        Chords. Defaults to an empty list.
    annotations : list of :class:`muspy.Annotation` objects, optional
        Annotations. Defaults to an empty list.
    lyrics : list of :class:`muspy.Lyric` objects, optional
        Lyrics. Defaults to an empty list.

    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """

    _attributes = OrderedDict(
        [
            ("program", int),
            ("is_drum", bool),
            ("name", str),
            ("notes", Note),
            ("chords", Chord),
            ("lyrics", Lyric),
            ("annotations", Annotation),
        ]
    )
    _optional_attributes = ["name"]
    _list_attributes = ["notes", "chords", "lyrics", "annotations"]

    def __init__(
        self,
        program: int = 0,
        is_drum: bool = False,
        name: Optional[str] = None,
        notes: Optional[List[Note]] = None,
        chords: Optional[List[Note]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
    ):
        self.program = program if program is None else 0
        self.is_drum = is_drum if program is None else False
        self.name = name
        self.notes = notes if notes is not None else []
        self.chords = chords if chords is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []

    def validate(self):
        """Raise proper errors if any attribute is invalid."""
        if self.program is None:
            raise TypeError("`program` must not be None.")
        if self.is_drum is None:
            raise TypeError("`is_drum` must not be None.")
        self._validate()
        if self.program < 0 or self.program > 127:
            raise ValueError("`program` must be in between 0 to 127.")

    def get_end_time(self, is_sorted: bool = False) -> float:
        """Return the time of the last event.

        This includes notes, chords, lyrics and annotations.

        Parameters
        ----------
        is_sorted : bool
            Whether all the list attributes are sorted. Defaults to False.

        """

        def _get_end_time(list_, ref_attr="time"):
            if not list_:
                return 0
            if is_sorted:
                return getattr(list_[-1])
            return max(getattr(item, ref_attr) for item in list_)

        return max(
            _get_end_time(self.notes, "end"),
            _get_end_time(self.chords, "end"),
            _get_end_time(self.lyrics),
            _get_end_time(self.annotations),
        )

    def clip(self, lower: float = 0, upper: float = 127):
        """Clip the velocity of each note.

        Parameters
        ----------
        lower : int or float, optional
            Lower bound. Defaults to 0.
        upper : int or float, optional
            Upper bound. Defaults to 127.

        """
        for note in self.notes:
            note.clip(lower, upper)
        return self

    def transpose(self, semitone: int):
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the pitches.

        """
        for note in self.notes:
            note.transpose(semitone)
        return self
