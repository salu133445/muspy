"""Core classes.

This module defines the core classes of MusPy.

Classes
-------

- Annotation
- Chord
- KeySignature
- Lyric
- Metadata
- Note
- Tempo
- TimeSignature
- Track


Variables
---------

- DEFAULT_VELOCITY

"""
from collections import OrderedDict
from typing import Any, List, Optional

from .base import Base, ComplexBase
from .schemas import DEFAULT_SCHEMA_VERSION

DEFAULT_VELOCITY = 64

__all__ = [
    "Annotation",
    "Chord",
    "DEFAULT_VELOCITY",
    "KeySignature",
    "Lyric",
    "Metadata",
    "Note",
    "Tempo",
    "TimeSignature",
    "Track",
]

# pylint: disable=super-init-not-called


class Metadata(Base):
    """A container for metadata.

    Attributes
    ----------
    schema_version : str
        Schema version. Defaults to the latest version.
    title : str, optional
        Song title.
    creators : list of str, optional
        Creator(s) of the song.
    copyright : str, optional
        Copyright notice.
    collection : str, optional
        Name of the collection.
    source_filename : str, optional
        Name of the source file.
    source_format : str, optional
        Format of the source file.

    """

    _attributes = OrderedDict(
        [
            ("schema_version", str),
            ("title", str),
            ("creators", str),
            ("copyright", str),
            ("collection", str),
            ("source_filename", str),
            ("source_format", str),
        ]
    )
    _optional_attributes = [
        "title",
        "creators",
        "copyright",
        "collection",
        "source_filename",
        "source_format",
    ]
    _list_attributes = ["creators"]

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        title: Optional[str] = None,
        creators: Optional[List[str]] = None,
        copyright: Optional[str] = None,
        collection: Optional[str] = None,
        source_filename: Optional[str] = None,
        source_format: Optional[str] = None,
    ):
        # pylint: disable=redefined-builtin
        self.schema_version = schema_version
        self.title = title
        self.creators = creators if creators is not None else []
        self.copyright = copyright
        self.collection = collection
        self.source_filename = source_filename
        self.source_format = source_format


class Tempo(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int
        Start time of the tempo, in time steps.
    qpm : float
        Tempo in qpm (quarters per minute).

    """

    _attributes = OrderedDict([("time", int), ("qpm", (int, float))])
    _sort_attributes = ["time"]

    def __init__(self, time: int, qpm: float):
        self.time = time
        self.qpm = float(qpm)

    def __eq__(self, other):
        return self.time == other.time and self.qpm == other.qpm

    def _validate(self, attr: str):
        super()._validate(attr)
        if attr == "qpm" and self.qpm <= 0:
            raise ValueError("`qpm` must be positive.")


class KeySignature(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int
        Start time of the key signature, in time steps or seconds.
    root : int, optional
        Root of the key signature.
    mode : str, optional
        Mode of the key signature.
    fifths : int, optional
        Number of flats or sharps. Positive numbers for sharps and negative
        numbers for flats.
    root_str : str, optional
        Root of the key signature as a string.

    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("root", int),
            ("mode", str),
            ("fifths", int),
            ("root_str", str),
        ]
    )
    _optional_attributes = ["root", "mode", "fifths", "root_str"]
    _sort_attributes = ["time"]

    def __init__(
        self,
        time: int,
        root: Optional[int] = None,
        mode: Optional[str] = None,
        fifths: Optional[int] = None,
        root_str: Optional[str] = None,
    ):
        self.time = time
        self.root = root
        self.mode = mode
        self.fifths = fifths
        self.root_str = root_str


class TimeSignature(Base):
    """A container for time signature.

    Attributes
    ----------
    time : int
        Start time of the time signature, in time steps or seconds.
    numerator : int
        Numerator of the time signature.
    denominator : int
        Denominator of the time signature.

    """

    _attributes = OrderedDict(
        [("time", int), ("numerator", int), ("denominator", int)]
    )
    _sort_attributes = ["time"]

    def __init__(self, time: int, numerator: int, denominator: int):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

    def _validate(self, attr: str):
        super()._validate(attr)
        if attr == "numerator" and self.numerator < 1:
            raise ValueError("`numerator` must be positive.")
        if attr == "denominator" and self.denominator < 1:
            raise ValueError("`denominator` must be positive.")


class Lyric(Base):
    """A container for lyric.

    Attributes
    ----------
    time : int
        Start time of the lyric, in time steps or seconds.
    lyric : str
        Lyric (sentence, word, syllable, etc.).

    """

    _attributes = OrderedDict([("time", int), ("lyric", str)])
    _sort_attributes = ["time"]

    def __init__(self, time: int, lyric: str):
        self.time = time
        self.lyric = lyric


class Annotation(Base):
    """A container for annotation.

    Attributes
    ----------
    time : int
        Start time of the annotation, in time steps or seconds.
    annotation : any object
        Annotation of any type.
    group : str, optional
        Group name for better organizing the annotations.

    """

    _attributes = _attributes = OrderedDict(
        [("time", int), ("annotation", str)]
    )
    _optional_attributes = ["group"]
    _sort_attributes = ["time"]

    def __init__(
        self, time: int, annotation: Any, group: Optional[str] = None
    ):
        self.time = time
        self.annotation = annotation
        self.group = group


class Note(Base):
    """A container for note.

    Attributes
    ----------
    time : int
        Start time of the note, in time steps.
    duration : int
        Duration of the note, in time steps.
    pitch : int
        Note pitch, as a MIDI note number.
    velocity : int, optional
        Note velocity. Defaults to `muspy.DEFAULT_VELOCITY`.
    pitch_str : str
        Note pitch as a string, useful for distinguishing C# and Db.

    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("duration", int),
            ("pitch", int),
            ("velocity", int),
            ("pitch_str", str),
        ]
    )
    _optional_attributes = ["velocity", "pitch_str"]
    _sort_attributes = ["time", "duration", "pitch"]

    def __init__(
        self,
        time: int,
        duration: int,
        pitch: int,
        velocity: Optional[int] = None,
        pitch_str: Optional[str] = None,
    ):
        self.time = time
        self.duration = duration
        self.pitch = pitch
        self.velocity = velocity if velocity is not None else DEFAULT_VELOCITY
        self.pitch_str = pitch_str

    @property
    def end(self):
        """End time of the note."""
        return self.time + self.duration

    @end.setter
    def end(self, end):
        """Setter for end time."""
        self.duration = end - self.time

    @property
    def start(self):
        """Start time of the note."""
        return self.time

    @start.setter
    def start(self, start):
        """Setter for start time."""
        self.time = start

    def _validate(self, attr: str):
        super()._validate(attr)
        if attr == "duration" and self.duration < 0:
            raise ValueError("`duration` must be nonnegative.")
        if attr == "pitch" and (self.pitch < 0 or self.pitch > 127):
            raise ValueError("`pitch` must be in between 0 to 127.")
        if attr == "velocity" and (self.velocity < 0 or self.velocity > 127):
            raise ValueError("`velocity` must be in between 0 to 127.")

    def _adjust_time(self, func, attr):
        if attr == "time":
            self.time = func(self.time)
        elif attr == "duration":
            self.duration = func(self.duration)

    def transpose(self, semitone: int) -> "Note":
        """Transpose the note by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the note. A positive value
            raises the pitch, while a negative value lowers the pitch.

        Returns
        -------
        Object itself.

        """
        self.pitch += semitone
        return self

    def clip(self, lower: int = 0, upper: int = 127) -> "Note":
        """Clip the velocity of the note.

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
        assert upper >= lower, "`upper` must be greater than `lower`."
        if self.velocity > upper:
            self.velocity = upper
        elif self.velocity < lower:
            self.velocity = lower
        return self


class Chord(Base):
    """A container for chord.

    Attributes
    ----------
    time : int
        Start time of the chord, in time steps.
    duration : int
        Duration of the chord, in time steps.
    pitches : list of int
        Note pitches, as MIDI note numbers.
    velocity : int, optional
        Chord velocity. Defaults to `muspy.DEFAULT_VELOCITY`.
    pitches_str : list of str
        Note pitches as strings, useful for distinguishing C# and Db.

    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("duration", int),
            ("pitches", int),
            ("velocity", int),
            ("pitches_str", str),
        ]
    )
    _optional_attributes = ["velocity", "pitches_str"]
    _list_attributes = ["pitches", "pitches_str"]
    _sort_attributes = ["time", "duration"]

    def __init__(
        self,
        time: int,
        duration: int,
        pitches: List[int],
        velocity: Optional[int] = None,
        pitches_str: Optional[List[int]] = None,
    ):
        self.time = time
        self.duration = duration
        self.pitches = pitches
        self.velocity = velocity if velocity is not None else DEFAULT_VELOCITY
        self.pitches_str = pitches_str

    @property
    def end(self):
        """End time of the chord."""
        return self.time + self.duration

    @end.setter
    def end(self, end):
        """Setter for end time."""
        self.duration = end - self.time

    @property
    def start(self):
        """Start time of the chord."""
        return self.time

    @start.setter
    def start(self, start):
        """Setter for start time."""
        self.time = start

    def _validate(self, attr: str):
        super()._validate(attr)
        if attr == "duration" and self.duration < 0:
            raise ValueError("`duration` must be nonnegative.")
        if attr == "pitches":
            for pitch in self.pitches:
                if pitch < 0 or pitch > 127:
                    raise ValueError(
                        "`pitches` must be a list of integers between 0 to "
                        "127."
                    )
        if attr == "velocity" and (self.velocity < 0 or self.velocity > 127):
            raise ValueError("`velocity` must be in between 0 to 127.")

    def _adjust_time(self, func, attr):
        if attr == "time":
            self.time = func(self.time)
        elif attr == "duration":
            self.duration = func(self.duration)

    def transpose(self, semitone: int) -> "Chord":
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value raises
            the pitches, while a negative value lowers the pitches.

        Returns
        -------
        Object itself.

        """
        self.pitches += [pitch + semitone for pitch in self.pitches]
        return self

    def clip(self, lower: int = 0, upper: int = 127) -> "Chord":
        """Clip the velocity of the chord.

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
        assert upper >= lower, "`upper` must be greater than `lower`."
        if self.velocity > upper:
            self.velocity = upper
        elif self.velocity < lower:
            self.velocity = lower
        return self


class Track(ComplexBase):
    """A container for music track.

    Indexing a Track object gives the note of a certain index. That is,
    `track[idx]` is equivalent to `track.notes[idx]`, while the latter is
    recommended for readability.

    Attributes
    ----------
    program : int, 0-127, optional
        Program number according to General MIDI specification [1]_.
        Defaults to 0 (Acoustic Grand Piano).
    is_drum : bool, optional
        Whether it is a percussion track. Defaults to False.
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

    Tip
    ---
    Indexing a Track object gives the note of a certain index. That is,
    `track[idx]` is equivalent to `track.notes[idx]`. Length of a Track
    object is the number of notes. That is, `len(track)`  is equivalent to
    `len(track.notes)`.

    References
    ----------
    .. [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

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
    _optional_attributes = ["name", "notes", "chords", "lyrics", "annotations"]
    _list_attributes = ["notes", "chords", "lyrics", "annotations"]
    _sort_attributes = ["is_drum", "program"]

    def __init__(
        self,
        program: int = 0,
        is_drum: bool = False,
        name: Optional[str] = None,
        notes: Optional[List[Note]] = None,
        chords: Optional[List[Chord]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
    ):
        self.program = program if program is not None else 0
        self.is_drum = is_drum if program is not None else False
        self.name = name
        self.notes = notes if notes is not None else []
        self.chords = chords if chords is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []

    def __len__(self) -> int:
        return len(self.notes)

    def __getitem__(self, key: int) -> Note:
        return self.notes[key]

    def __setitem__(self, key: int, value: Note):
        self.notes[key] = value

    def validate(self, attr: Optional[str] = None) -> "Track":
        """Raise proper errors if a certain attribute is invalid.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. If None, validate all attributes. Defaults
            to None.

        """
        super().validate()
        if self.program is None:
            raise TypeError("`program` must not be None.")
        if self.is_drum is None:
            raise TypeError("`is_drum` must not be None.")
        if self.program < 0 or self.program > 127:
            raise ValueError("`program` must be in between 0 to 127.")
        return self

    def get_end_time(self, is_sorted: bool = False) -> int:
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
                return getattr(list_[-1], ref_attr)
            return max(getattr(item, ref_attr) for item in list_)

        return max(
            _get_end_time(self.notes, "end"),
            _get_end_time(self.chords, "end"),
            _get_end_time(self.lyrics),
            _get_end_time(self.annotations),
        )

    def clip(self, lower: int = 0, upper: int = 127) -> "Track":
        """Clip the velocity of each note.

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
        for note in self.notes:
            note.clip(lower, upper)
        return self

    def transpose(self, semitone: int) -> "Track":
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the pitches.

        Returns
        -------
        Object itself.

        """
        for note in self.notes:
            note.transpose(semitone)
        return self
