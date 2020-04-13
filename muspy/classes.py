"""Core classes."""
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, List, Mapping, Optional, Union

from .schemas import DEFAULT_SCHEMA_VERSION

DEFAULT_BEAT_RESOLUTION = 24

# pylint: disable=super-init-not-called


def validate_list(list_: List):
    """Validate a list of objects by calling their method `validate`."""
    for item in list_:
        item.validate()


def remove_invalid_from_list(list_: List) -> List:
    """Return a list with invalid items removed."""
    return [item for item in list_ if item.is_valid()]


class Base(ABC):
    """Base container for MusPy objects.

    It implements the following three handy methods.

    - Intuitive and meaningful `__repr__` in the form of
      `class_name(attr_1=value_1, attr_2=value_2,...)`.
    - Method `from_dict` that sets the attributes by the corresponding values
      in a dictionary.
    - Method `to_ordered_dict` that returns the object as an OrderedDict.

    Notes
    -----
    This is the base class for MusPy objects. To add a new class, please
    inherit from this class and set the class variables `_attributes`
    properly. The list `_attributes` contains all the attribute keys of the
    class so that the above methods can be implemented.

    """

    _attributes: List[str] = []

    @abstractmethod
    def __init__(self, **kwargs):
        raise NotImplementedError

    def __repr__(self):
        return (
            type(self).__name__
            + "("
            + ", ".join(
                [
                    key + "=" + repr(getattr(self, key))
                    for key in self._attributes
                ]
            )
            + ")"
        )

    @classmethod
    def from_dict(cls, dict_: Mapping):
        """Return an instance constructed from a dictionary.

        Parameters
        ----------
        dict_ : dict
            A dictionary that stores the attributes and their values as
            key-value pairs.

        """
        for key in cls._attributes:
            if key not in dict_:
                ValueError("Missing value for attribute {}.".format(key))
        return cls(**dict_)

    def to_ordered_dict(self) -> OrderedDict:
        """Return the object as an OrderedDict."""
        ordered_dict = OrderedDict()
        for key in self._attributes:
            value = getattr(self, key)
            if hasattr(value, "to_ordered_dict"):
                ordered_dict[key] = value.to_ordered_dict()
            elif isinstance(value, list):
                ordered_dict[key] = [
                    v.to_ordered_dict() if hasattr(v, "to_ordered_dict") else v
                    for v in value
                ]
            elif isinstance(value, dict):
                ordered_dict[key] = {
                    k: v.to_ordered_dict()
                    if hasattr(v, "to_ordered_dict")
                    else v
                    for k, v in value.items()
                }
            else:
                ordered_dict[key] = value
        return ordered_dict

    @abstractmethod
    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        raise NotImplementedError

    def is_valid(self):
        """Return True if all attributes are valid."""
        try:
            self.validate()
        except (TypeError, ValueError):
            return False
        return True


class SongInfo(Base):
    """A container for song information.

    Attributes
    ----------
    title : str, optional
        Song title.
    artist : str, optional
        Main artist of the song.
    composers : list of str, optional
        Composers of the song.

    """

    _attributes = ["title", "artist", "composers"]

    def __init__(
        self,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        composers: Optional[List[str]] = None,
    ):
        self.title = title
        self.artist = artist
        self.composers = composers

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.title, str):
            raise TypeError("`title` must be a string.")
        if not isinstance(self.artist, str):
            raise TypeError("`artist` must be a string.")
        if not isinstance(self.composers, list):
            raise TypeError("`composers` must be a list.")
        for composer in self.composers:
            if not isinstance(composer, str):
                raise TypeError("`composers` must be a list of string.")


class SourceInfo(Base):
    """A container for source information.

    Attributes
    ----------
    collection : str, optional
        Name of the collection name.
    filename : str, optional
        Path to the file in the collection.
    format : {'midi', 'musicxml'}, optional
        Format of the source file
    id : str, optional
        Unique ID of the file

    """

    _attributes = ["collection", "filename", "format", "id"]

    def __init__(
        self,
        collection: Optional[str] = None,
        filename: Optional[str] = None,
        format_: Optional[str] = None,
        id_: Optional[str] = None,
    ):
        self.collection = collection
        self.filename = filename
        self.format = format_
        self.id = id_

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.collection, str):
            raise TypeError("`collection` must be a string.")
        if not isinstance(self.filename, str):
            raise TypeError("`filename` must be a string.")
        if self.format is not None:
            if not isinstance(self.format, str):
                raise TypeError("`format` must be a string.")
            if self.format not in ("midi", "musicxml", None):
                raise ValueError("`format` must be one of 'midi', 'musicxml'.")


class MetaData(Base):
    """A container for meta data.

    Attributes
    ----------
    schema_version : str
        Schema version.
    song_info : :class:'muspy.SongInfo` object, optional
        Soong infomation.
    source_info : :class:'muspy.SourceInfo` object, optional
        Source infomation.

    """

    _attributes = ["schema_version", "song_info", "source_info"]

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        song_info: Optional[str] = None,
        source_info: Optional[str] = None,
    ):
        self.schema_version = schema_version
        self.song_info = song_info if song_info is not None else SongInfo()
        self.source_info = (
            source_info if source_info is not None else SourceInfo()
        )

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.schema_version, str):
            raise TypeError("`schema_version` must be a string.")
        if not isinstance(self.song_info, SongInfo):
            raise TypeError("`song_info` must be of type SongInfo.")
        if not isinstance(self.source_info, SourceInfo):
            raise TypeError("`source_info` must be of type SourceInfo.")
        self.song_info.validate()
        self.source_info.validate()


class TimingInfo(Base):
    """A container for song information.

    Attributes
    ----------
    is_symbolic_timing : bool
        If true, the timing is in time steps. Otherwise, it's in seconds.
    beat_resolution : int
        Time steps per beat (only effective when `is_symbolic_timing` is true).

    """

    _attributes = ["is_symbolic_timing", "beat_resolution"]

    def __init__(
        self,
        is_symbolic_timing: bool = True,
        beat_resolution: int = DEFAULT_BEAT_RESOLUTION,
    ):
        self.is_symbolic_timing = is_symbolic_timing
        self.beat_resolution = beat_resolution

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.is_symbolic_timing, bool):
            raise TypeError("`is_symbolic_timing` must be a boolean.")
        if not isinstance(self.beat_resolution, int):
            raise TypeError("`beat_resolution` must be an integer.")
        if self.beat_resolution < 1:
            raise ValueError("`beat_resolution` must be a positive integer.")


class Note(Base):
    """A container for note.

    Attributes
    ----------
    start : int or float
        Start time of the note, in time steps or seconds (see Note).
    end : int or float
        End time of the note, in time steps or seconds (see Note).
    pitch : int or float
        Note pitch, as a MIDI note number.
    velocity : int or float
        Note velocity.


    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["start", "end", "pitch", "velocity"]

    def __init__(
        self,
        start: Union[int, float],
        end: Union[int, float],
        pitch: Union[int, float],
        velocity: Union[int, float],
    ):
        self.start = start
        self.end = end
        self.pitch = pitch
        self.velocity = velocity

    @property
    def duration(self):
        """Duration of the note."""
        return self.end - self.start

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.start, (int, float)):
            raise TypeError("`start` must be an integer or a float.")
        if not isinstance(self.end, (int, float)):
            raise TypeError("`end` must be an integer or a float.")
        if not isinstance(self.pitch, int):
            raise TypeError("`pitch` must be an integer.")
        if not isinstance(self.velocity, int):
            raise TypeError("`velocity` must be an integer.")
        if self.start < 0:
            raise ValueError("`start` must be a positive number.")
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

    def clip(
        self, lower: Union[int, float] = 0, upper: Union[int, float] = 127
    ):
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


class Lyric(Base):
    """A container for lyric.

    Attributes
    ----------
    time : int or float
        Start time of the lyric, in time steps or seconds (see Note).
    lyric : str
        The lyric.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "lyric"]

    def __init__(self, time: Union[int, float], lyric: str):
        self.time = time
        self.lyric = lyric

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.time, (int, float)):
            raise TypeError("`time` must be an integer or a float.")
        if not isinstance(self.lyric, str):
            raise TypeError("`lyric` must be a string.")
        if self.time < 0:
            raise ValueError("`time` must be a positive number.")


class Annotation(Base):
    """A container for annotation.

    Attributes
    ----------
    time : int or float
        Start time of the annotation, in time steps or seconds (see Note).
    annotation : any object
        Annotation of any type.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "annotation"]

    def __init__(self, time: Union[int, float], annotation: Any):
        self.time = time
        self.annotation = annotation

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.time, (int, float)):
            raise TypeError("`time` must be an integer or a float.")
        if self.time < 0:
            raise ValueError("`time` must be a positive number.")


class TimeSignature(Base):
    """A container for time signature.

    Attributes
    ----------
    time : int or float
        Start time of the time signature, in time steps or seconds (see Note).
    numerator : int
        Numerator of the time signature.
    denominator : int
        Denominator of the time signature.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "numerator", "denominator"]

    def __init__(
        self, time: Union[int, float], numerator: int, denominator: int
    ):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.time, (int, float)):
            raise TypeError("`time` must be an integer or a float.")
        if not isinstance(self.numerator, int):
            raise TypeError("`numerator` must be an integer.")
        if not isinstance(self.denominator, int):
            raise TypeError("`denominator` must be an integer.")
        if self.numerator < 1:
            raise ValueError("`numerator` must be a positive number.")
        if self.denominator < 1:
            raise ValueError("`denominator` must be a positive number.")


class KeySignature(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int or float
        Start time of the key signature, in time steps or seconds (see Note).
    root : str
        Root of the key signature.
    mode : str
        Mode of the key signature.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "root", "mode"]

    def __init__(self, time: Union[int, float], root: str, mode: str):
        self.time = time
        self.root = root
        self.mode = mode

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.time, (int, float)):
            raise TypeError("`time` must be an integer or a float.")
        if not isinstance(self.root, str):
            raise TypeError("`root` must be an integer.")
        if not isinstance(self.mode, str):
            raise TypeError("`mode` must be an integer.")


class Tempo(Base):
    """A container for key signature.

    Attributes
    ----------
    time : int or float
        Start time of the key signature, in time steps or seconds (see Note).
    tempo : float
        Tempo in bpm (beats per minute)

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "tempo"]

    def __init__(self, time: Union[int, float], tempo: Union[int, float]):
        self.time = time
        self.tempo = float(tempo)

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.time, (int, float)):
            raise TypeError("`time` must be an integer or float.")
        if not isinstance(self.tempo, (int, float)):
            raise TypeError("`tempo` must be an integer or a float.")


class Track(Base):
    """A container for music track.

    Attributes
    ----------
    name : str
        Name of the track. Defaults to 'unknown'.
    program : int
        A program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand Piano).
    is_drum : bool
        A boolean indicating if it is a percussion track. Defaults to False.
    notes : list of :class:'muspy.Note` objects
        A list of notes.
    annotations : list of :class:'muspy.Annotation' objects
        A list of annotations.
    lyrics : list of :class:'muspy.Lyric' objects
        A list of lyrics.

    """

    _attributes = [
        "name",
        "program",
        "is_drum",
        "notes",
        "lyrics",
        "annotations",
    ]

    def __init__(
        self,
        name: str = "unknown",
        program: int = 0,
        is_drum: bool = False,
        notes: Optional[List[Note]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
    ):
        self.name = name
        self.program = program
        self.is_drum = is_drum
        self.notes = notes if notes is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.name, str):
            raise TypeError("`program` must be a string.")
        if not isinstance(self.program, int):
            raise TypeError("`program` must be an integer.")
        if self.program < 0 or self.program > 127:
            raise ValueError("`program` must be in between 0 to 127.")
        if not isinstance(self.is_drum, bool):
            raise TypeError("`is_drum` must be a boolean.")
        if not isinstance(self.notes, list):
            raise TypeError("`notes` must be a list.")
        if not isinstance(self.lyrics, list):
            raise TypeError("`lyrics` must be a list.")
        if not isinstance(self.annotations, list):
            raise TypeError("`annotations` must be a list.")
        validate_list(self.notes)
        validate_list(self.lyrics)
        validate_list(self.annotations)

    def remove_invalid(self):
        """Remove invalid objects, including notes, lyrics and annotations."""
        self.notes = remove_invalid_from_list(self.notes)
        self.lyrics = remove_invalid_from_list(self.lyrics)
        self.annotations = remove_invalid_from_list(self.annotations)

    def get_active_length(self, is_sorted=False) -> Union[int, float]:
        """Return the end time of the last note."""
        if is_sorted:
            return self.notes[-1].end
        return max([note.end for note in self.notes])

    def get_length(self, is_sorted=False) -> Union[int, float]:
        """Return the time of the last event.

        This includes notes onsets, note offsets, lyrics and annotations.

        """
        if is_sorted:
            return max(
                self.get_active_length(is_sorted),
                self.lyrics[-1].time,
                self.annotations[-1].time,
            )
        return max(
            self.get_active_length(is_sorted),
            max([lyric.time for lyric in self.lyrics]),
            max([annotation.time for annotation in self.annotations]),
        )

    def append(self, obj: Union[Note, Lyric, Annotation]):
        """Append an object to the correseponding list.

        Parameters
        ----------
        obj : Muspy objects (see below)
            Object to be appended. Supported object types are
            :class:`Muspy.Note`, :class:`Muspy.Annotation` and
            :class:`Muspy.Lyric` objects.

        """
        if isinstance(obj, Note):
            self.notes.append(obj)
        elif isinstance(obj, Lyric):
            self.lyrics.append(obj)
        elif isinstance(obj, Annotation):
            self.annotations.append(obj)
        else:
            raise TypeError(
                "Expect Note, Lyric or Annotation object, but got {}.".format(
                    type(obj)
                )
            )

    def clip(
        self, lower: Union[int, float] = 0, upper: Union[int, float] = 127
    ):
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

    def sort(self):
        """Sort the time-stamped objects with respect to event time.

        This will sort notes, lyrics and annotations.

        """
        self.notes.sort(key=lambda x: x.start)
        self.lyrics.sort(key=lambda x: x.time)
        self.annotations.sort(key=lambda x: x.time)

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
