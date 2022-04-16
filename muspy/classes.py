"""Core classes.

This module defines the core classes of MusPy.

Classes
-------

- Annotation
- Barline
- Beat
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
from typing import Any, Callable, List, TypeVar

from .base import Base, ComplexBase
from .schemas import DEFAULT_SCHEMA_VERSION

DEFAULT_VELOCITY = 64
NoteT = TypeVar("NoteT", bound="Note")
ChordT = TypeVar("ChordT", bound="Chord")
TrackT = TypeVar("TrackT", bound="Track")

__all__ = [
    "Annotation",
    "Barline",
    "Beat",
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


def get_end_time(list_: List, is_sorted: bool = False, attr: str = "time"):
    """Return the end time of a list of objects.

    Parameters
    ----------
    list_ : list
        List of objects.
    is_sorted : bool, default: False
        Whether the list is sorted.
    attr : str, default: 'time'
        Attribute to look for.

    """
    if not list_:
        return 0
    if is_sorted:
        return getattr(list_[-1], attr)
    return max(getattr(item, attr) for item in list_)


def _trim_list(list_: List, end: int):
    new_list = []
    for item in list_:
        if item.time >= end:
            continue
        if item.end > end:
            item.end = end
        new_list.append(item)
    return new_list


class Metadata(Base):
    """A container for metadata.

    Attributes
    ----------
    schema_version : str, default: `muspy.DEFAULT_SCHEMA_VERSION`
        Schema version.
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
        title: str = None,
        creators: List[str] = None,
        copyright: str = None,
        collection: str = None,
        source_filename: str = None,
        source_format: str = None,
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
    """A container for key signatures.

    Attributes
    ----------
    time : int
        Start time of the tempo, in time steps.
    qpm : float
        Tempo in qpm (quarters per minute).

    """

    _attributes = OrderedDict([("time", int), ("qpm", (float, int))])

    def __init__(self, time: int, qpm: float):
        self.time = time
        self.qpm = float(qpm)

    def _validate(self, attr: str, recursive: bool):
        super()._validate(attr, recursive)
        if attr == "qpm" and self.qpm <= 0:
            raise ValueError("`qpm` must be positive.")


class KeySignature(Base):
    """A container for key signatures.

    Attributes
    ----------
    time : int
        Start time of the key signature, in time steps.
    root : int, optional
        Root (tonic) of the key signature.
    mode : str, optional
        Mode of the key signature.
    fifths : int, optional
        Number of sharps or flats. Positive numbers for sharps and
        negative numbers for flats.
    root_str : str, optional
        Root of the key signature as a string.

    Note
    ----
    A key signature can be specified either by its root (`root`) or the
    number of sharps or flats (`fifths`) along with its mode.

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

    def __init__(
        self,
        time: int,
        root: int = None,
        mode: str = None,
        fifths: int = None,
        root_str: str = None,
    ):
        self.time = time
        self.root = root
        self.mode = mode
        self.fifths = fifths
        self.root_str = root_str


class TimeSignature(Base):
    """A container for time signatures.

    Attributes
    ----------
    time : int
        Start time of the time signature, in time steps.
    numerator : int
        Numerator of the time signature.
    denominator : int
        Denominator of the time signature.

    """

    _attributes = OrderedDict(
        [("time", int), ("numerator", int), ("denominator", int)]
    )

    def __init__(self, time: int, numerator: int, denominator: int):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

    def _validate(self, attr: str, recursive: bool):
        super()._validate(attr, recursive)
        if attr == "numerator" and self.numerator < 1:
            raise ValueError("`numerator` must be positive.")
        if attr == "denominator" and self.denominator < 1:
            raise ValueError("`denominator` must be positive.")


class Beat(Base):
    """A container for beats.

    Attributes
    ----------
    time : int
        Time of the beat, in time steps.

    """

    _attributes = OrderedDict([("time", int)])

    def __init__(self, time: int):
        self.time = time


class Barline(Base):
    """A container for barlines.

    Attributes
    ----------
    time : int
        Time of the barline, in time steps.

    """

    _attributes = OrderedDict([("time", int)])

    def __init__(self, time: int):
        self.time = time


class Lyric(Base):
    """A container for lyrics.

    Attributes
    ----------
    time : int
        Start time of the lyric, in time steps.
    lyric : str
        Lyric (sentence, word, syllable, etc.).

    """

    _attributes = OrderedDict([("time", int), ("lyric", str)])

    def __init__(self, time: int, lyric: str):
        self.time = time
        self.lyric = lyric


class Annotation(Base):
    """A container for annotations.

    Attributes
    ----------
    time : int
        Start time of the annotation, in time steps.
    annotation : any
        Annotation of any type.
    group : str, optional
        Group name (for better organizing the annotations).

    """

    _attributes = OrderedDict(
        [("time", int), ("annotation", object), ("group", str)]
    )
    _optional_attributes = ["group"]

    def __init__(self, time: int, annotation: Any, group: str = None):
        self.time = time
        self.annotation = annotation
        self.group = group


class Note(Base):
    """A container for notes.

    Attributes
    ----------
    time : int
        Start time of the note, in time steps.
    pitch : int
        Note pitch, as a MIDI note number. Valid values are 0 to 127.
    duration : int
        Duration of the note, in time steps.
    velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Note velocity. Valid values are 0 to 127.
    pitch_str : str, optional
        Note pitch as a string, useful for distinguishing, e.g., C# and
        Db.

    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("pitch", int),
            ("duration", int),
            ("velocity", int),
            ("pitch_str", str),
        ]
    )
    _optional_attributes = ["velocity", "pitch_str"]

    def __init__(
        self,
        time: int,
        pitch: int,
        duration: int,
        velocity: int = None,
        pitch_str: str = None,
    ):
        self.time = time
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity if velocity is not None else DEFAULT_VELOCITY
        self.pitch_str = pitch_str

    @property
    def start(self):
        """Start time of the note."""
        return self.time

    @start.setter
    def start(self, start):
        """Setter for start time."""
        self.time = start

    @property
    def end(self):
        """End time of the note."""
        return self.time + self.duration

    @end.setter
    def end(self, end):
        """Setter for end time."""
        self.duration = end - self.time

    def _validate(self, attr: str, recursive: bool):
        super()._validate(attr, recursive)
        if attr == "pitch" and (self.pitch < 0 or self.pitch > 127):
            raise ValueError("`pitch` must be in between 0 to 127.")
        if attr == "duration" and self.duration < 0:
            raise ValueError("`duration` must be nonnegative.")
        if attr == "velocity" and (self.velocity < 0 or self.velocity > 127):
            raise ValueError("`velocity` must be in between 0 to 127.")

    def _adjust_time(
        self, func: Callable[[int], int], attr: str, recursive: bool
    ):
        raise NotImplementedError

    def adjust_time(
        self: NoteT,
        func: Callable[[int], int],
        attr: str = None,
        recursive: bool = True,
    ) -> NoteT:
        """Adjust the timing of the note.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old
            timing, i.e., `new_time = func(old_time)`.
        attr : str, optional
            Attribute to adjust. Defaults to adjust all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is not None and attr != "time":
            raise AttributeError(f"'Note' object has no attribute '{attr}'")

        old_time = self.time
        self.time = func(self.time)
        self.duration = func(old_time + self.duration) - self.time
        return self

    def transpose(self: NoteT, semitone: int) -> NoteT:
        """Transpose the note by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the note. A positive value
            raises the pitch, while a negative value lowers the pitch.

        Returns
        -------
        Object itself.

        """
        self.pitch += semitone
        return self

    def clip(self: NoteT, lower: int = 0, upper: int = 127) -> NoteT:
        """Clip the velocity of the note.

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
        assert upper >= lower, "`upper` must be greater than `lower`."
        if self.velocity > upper:
            self.velocity = upper
        elif self.velocity < lower:
            self.velocity = lower
        return self


class Chord(Base):
    """A container for chords.

    Attributes
    ----------
    time : int
        Start time of the chord, in time steps.
    pitches : list of int
        Note pitches, as MIDI note numbers. Valid values are 0 to 127.
    duration : int
        Duration of the chord, in time steps.
    velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Chord velocity. Valid values are 0 to 127.
    pitches_str : list of str, optional
        Note pitches as strings, useful for distinguishing, e.g., C# and
        Db.

    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("pitches", int),
            ("duration", int),
            ("velocity", int),
            ("pitches_str", str),
        ]
    )
    _optional_attributes = ["velocity", "pitches_str"]

    def __init__(
        self,
        time: int,
        pitches: List[int],
        duration: int,
        velocity: int = None,
        pitches_str: List[int] = None,
    ):
        self.time = time
        self.pitches = pitches
        self.duration = duration
        self.velocity = velocity if velocity is not None else DEFAULT_VELOCITY
        self.pitches_str = pitches_str

    @property
    def start(self):
        """Start time of the chord."""
        return self.time

    @start.setter
    def start(self, start):
        """Setter for start time."""
        self.time = start

    @property
    def end(self):
        """End time of the chord."""
        return self.time + self.duration

    @end.setter
    def end(self, end):
        """Setter for end time."""
        self.duration = end - self.time

    def _validate(self, attr: str, recursive: bool):
        super()._validate(attr, recursive)
        if attr == "pitches":
            for pitch in self.pitches:
                if pitch < 0 or pitch > 127:
                    raise ValueError(
                        "`pitches` must be a list of integers between 0 to "
                        "127."
                    )
        if attr == "duration" and self.duration < 0:
            raise ValueError("`duration` must be nonnegative.")
        if attr == "velocity" and (self.velocity < 0 or self.velocity > 127):
            raise ValueError("`velocity` must be in between 0 to 127.")

    def _adjust_time(
        self, func: Callable[[int], int], attr: str, recursive: bool
    ):
        raise NotImplementedError

    def adjust_time(
        self: ChordT,
        func: Callable[[int], int],
        attr: str = None,
        recursive: bool = True,
    ) -> ChordT:
        """Adjust the timing of the chord.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old
            timing, i.e., `new_time = func(old_time)`.
        attr : str, optional
            Attribute to adjust. Defaults to adjust all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is not None and attr != "time":
            raise AttributeError(f"'Note' object has no attribute '{attr}'")

        old_time = self.time
        self.time = func(self.time)
        self.duration = func(old_time + self.duration) - self.time
        return self

    def transpose(self: ChordT, semitone: int) -> ChordT:
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the
            pitches.

        Returns
        -------
        Object itself.

        """
        self.pitches += [pitch + semitone for pitch in self.pitches]
        return self

    def clip(self: ChordT, lower: int = 0, upper: int = 127) -> ChordT:
        """Clip the velocity of the chord.

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
        assert upper >= lower, "`upper` must be greater than `lower`."
        if self.velocity > upper:
            self.velocity = upper
        elif self.velocity < lower:
            self.velocity = lower
        return self


class Track(ComplexBase):
    """A container for music track.

    Attributes
    ----------
    program : int, default: 0 (Acoustic Grand Piano)
        Program number, according to General MIDI specification [1]_.
        Valid values are 0 to 127.
    is_drum : bool, default: False
        Whether it is a percussion track.
    name : str, optional
        Track name.
    notes : list of :class:`muspy.Note`, default: []
        Musical notes.
    chords : list of :class:`muspy.Chord`, default: []
        Chords.
    annotations : list of :class:`muspy.Annotation`, default: []
        Annotations.
    lyrics : list of :class:`muspy.Lyric`, default: []
        Lyrics.

    Note
    ----
    Indexing a Track object returns the note at a certain index. That
    is, ``track[idx]`` returns ``track.notes[idx]``. Length of a Track
    object is the number of notes. That is, ``len(track)`` returns
    ``len(track.notes)``.

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

    def __init__(
        self,
        program: int = 0,
        is_drum: bool = False,
        name: str = None,
        notes: List[Note] = None,
        chords: List[Chord] = None,
        lyrics: List[Lyric] = None,
        annotations: List[Annotation] = None,
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

    def __delitem__(self, key: int):
        del self.notes[key]

    def _validate(self, attr: str, recursive: bool):
        super()._validate(attr, recursive)
        if attr == "program" and self.program < 0 or self.program > 127:
            raise ValueError("`program` must be in between 0 to 127.")

    def get_end_time(self, is_sorted: bool = False) -> int:
        """Return the time of the last event.

        This includes notes, chords, lyrics and annotations.

        Parameters
        ----------
        is_sorted : bool, default: False
            Whether all the list attributes are sorted.

        """
        return max(
            get_end_time(self.notes, is_sorted, "end"),
            get_end_time(self.chords, is_sorted, "end"),
            get_end_time(self.lyrics, is_sorted),
            get_end_time(self.annotations, is_sorted),
        )

    def clip(self: TrackT, lower: int = 0, upper: int = 127) -> TrackT:
        """Clip the velocity of each note.

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
        for note in self.notes:
            note.clip(lower, upper)
        return self

    def transpose(self: TrackT, semitone: int) -> TrackT:
        """Transpose the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the
            pitches.

        Returns
        -------
        Object itself.

        """
        for note in self.notes:
            note.transpose(semitone)
        return self

    def trim(self: TrackT, end: int) -> TrackT:
        """Trim the track.

        Parameters
        ----------
        end : int
            End time, excluding (i.e, the max time will be `end` - 1).

        Returns
        -------
        Object itself.

        """
        self.notes = _trim_list(self.notes, end)
        self.chords = _trim_list(self.chords, end)
        self.lyrics = [x for x in self.lyrics if x.time < end]
        self.annotations = [x for x in self.annotations if x.time < end]
        return self
