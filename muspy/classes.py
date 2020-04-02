"""Core functionality."""
from collections import OrderedDict

from muspy.schemas import SCHEMA_VERSION

DEFAULT_BEAT_RESOLUTION = 24


class Base:
    """Base container."""

    _attributes = []

    def __repr__(self):
        return (
            type(self).__name__
            + "("
            + ", ".join(
                [key + "=" + repr(getattr(self, key)) for key in self._attributes]
            )
            + ")"
        )

    def to_ordered_dict(self):
        """Convert to OrderedDict."""
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
                    k: v.to_ordered_dict() if hasattr(v, "to_ordered_dict") else v
                    for k, v in value.items()
                }
            else:
                ordered_dict[key] = value
        return ordered_dict


class SongInfo(Base):
    """A container for song information.

    Attributes
    ----------
    title : str
        Song title.
    artist : str
        Main artist of the song.
    composers : list of str
        Composers of the song.
    """

    _attributes = ["title", "artist", "composers"]

    def __init__(self, title=None, artist=None, composers=None):
        self.title = title
        self.artist = artist
        self.composers = composers


class SourceInfo(Base):
    """A container for source information.

    Attributes
    ----------
    collection : str
        Name of the collection name.
    filename : str
        Path to the file in the collection.
    format : {'midi', 'musicxml', 'abc', None}
        Format of the source file
    id : str
        Unique ID of the file
    """

    _attributes = ["collection", "filename", "format", "id"]

    def __init__(self, collection=None, filename=None, format_=None, id_=None):
        self.collection = collection
        self.filename = filename
        self.format = format_
        self.id = id_


class MetaData(Base):
    """A container for meta data.

    Attributes
    ----------
    version : str
        Song title.
    song : :class:'muspy.SongInfo` object
        Soong infomation.
    source : :class:'muspy.SourceInfo` object
        Source infomation.
    """

    _attributes = ["schema_version", "song", "source"]

    def __init__(self, schema_version=SCHEMA_VERSION, song=None, source=None):
        self.schema_version = schema_version
        self.song = song if song is not None else SongInfo()
        self.source = source if source is not None else SourceInfo()


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
        self, is_symbolic_timing=True, beat_resolution=DEFAULT_BEAT_RESOLUTION
    ):
        self.is_symbolic_timing = is_symbolic_timing
        self.beat_resolution = beat_resolution


class Note(Base):
    """A container for note.

    Attributes
    ----------
    start : float
        Start time of the note, in time steps or seconds (see Note).
    end : float
        End time of the note, in time steps or seconds (see Note).
    pitch : int
        Note pitch, as a MIDI note number.
    velocity : int
        Note velocity.


    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["start", "end", "pitch", "velocity"]

    def __init__(self, start, end, pitch, velocity):
        self.start = start
        self.end = end
        self.pitch = pitch
        self.velocity = velocity

    @property
    def duration(self):
        """Duration of the note."""
        return self.end - self.start


class Annotation(Base):
    """A container for annotation.

    Attributes
    ----------
    time : float
        Start time of the annotation, in time steps or seconds (see Note).
    annotation : any object
        Annotation of any type.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "annotation"]

    def __init__(self, time, annotation):
        self.time = time
        self.annotation = annotation


class Lyric(Base):
    """A container for lyric.

    Attributes
    ----------
    time : float
        Start time of the lyric, in time steps or seconds (see Note).
    lyric : str
        The lyric.

    Note
    ----
    The timing unit is determined by higher-level objects."""

    _attributes = ["time", "lyric"]

    def __init__(self, time, lyric):
        if not isinstance(lyric, str):
            raise TypeError(
                "Expect `lyric` of str type, but got {}.".format(type(lyric))
            )
        self.time = time
        self.lyric = lyric


class TimeSignature(Base):
    """A container for time signature.

    Attributes
    ----------
    time : float
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

    def __init__(self, time, numerator, denominator):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator


class KeySignature(Base):
    """A container for key signature.

    Attributes
    ----------
    time : float
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

    def __init__(self, time, root, mode):
        self.time = time
        self.root = root
        self.mode = mode


class Tempo(Base):
    """A container for key signature.

    Attributes
    ----------
    time : float
        Start time of the key signature, in time steps or seconds (see Note).
    tempo : float
        Tempo in bpm (beats per minute)

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    _attributes = ["time", "tempo"]

    def __init__(self, time, tempo):
        self.time = time
        self.tempo = tempo


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

    _attributes = ["name", "program", "is_drum", "notes", "lyrics", "annotations"]

    def __init__(
        self,
        name="unknown",
        program=0,
        is_drum=False,
        notes=None,
        lyrics=None,
        annotations=None,
    ):
        self.name = name
        self.program = program
        self.is_drum = is_drum
        self.notes = notes if notes is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []

    def append(self, obj):
        """Append a note or an annotation."""
        if isinstance(obj, Note):
            self.notes.append(obj)
        elif isinstance(obj, Annotation):
            self.annotations.append(obj)
        elif isinstance(obj, Lyric):
            self.lyrics.append(obj)
        else:
            raise TypeError(
                "Expect Note or Annotation object, but got {}.".format(type(obj))
            )

    def sort(self):
        """Sort the notes and annotations with respect to event time."""
        self.notes.sort(key=lambda x: x.start)
        self.lyrics.sort(key=lambda x: x.time)
        self.annotations.sort(key=lambda x: x.time)
