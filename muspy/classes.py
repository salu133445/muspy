"""Core functionality."""
from muspy.schemas import SCHEMA_VERSION

DEFAULT_BEAT_RESOLUTION = 24


class SongInfo:
    """
    A container for song information.

    Attributes
    ----------
    title : str
        Song title.
    artist : str
        Main artist of the song.
    composers : list of str
        Composers of the song.
    """

    def __init__(self, title=None, artist=None, composers=None):
        self.title = title
        self.artist = artist
        self.composers = composers

    def __repr__(self):
        return "SongInfo(title={}, artist={}, composers={})".format(
            self.title, self.artist, self.composers
        )


class SourceInfo:
    """
    A container for source information.

    Attributes
    ----------
    id_ : str
        Unique ID of the file
    collection : str
        Name of the collection name.
    filename : str
        Path to the file in the collection.
    format_ : {'midi', 'musicxml', 'abc', None}
        Format of the source file
    """

    def __init__(self, id_=None, collection=None, filename=None, format_=None):
        self.id = id_
        self.collection = collection
        self.filename = filename
        self.format = format_

    def __repr__(self):
        return "SourceInfo(src_id={}, collection={}, filename={}, format={})".format(
            self.id, self.collection, self.filename, self.format
        )


class MetaData:
    """
    A container for meta data.

    Attributes
    ----------
    version : str
        Song title.
    song_info : :class:'muspy.SongInfo` object
        Soong infomation.
    source_info : :class:'muspy.SourceInfo` object
        Source infomation.
    """

    def __init__(self, schema_version=SCHEMA_VERSION, song_info=None, source_info=None):
        self.schema_version = schema_version
        self.song = song_info if song_info is not None else SongInfo()
        self.source = source_info if source_info is not None else SourceInfo()

    def __repr__(self):
        return "MetaData(schema_version={}, song_info={}, source_info={})".format(
            self.schema_version, self.song, self.source
        )


class TimingInfo:
    """
    A container for song information.

    Attributes
    ----------
    is_symbolic_timing : bool
        If true, the timing is in time steps. Otherwise, it's in seconds.
    beat_resolution : int
        Time steps per beat (only effective when `is_symbolic_timing` is true).
    """

    def __init__(
        self, is_symbolic_timing=True, beat_resolution=DEFAULT_BEAT_RESOLUTION
    ):
        self.is_symbolic_timing = is_symbolic_timing
        self.beat_resolution = beat_resolution

    def __repr__(self):
        return "TimingInfo(is_symbolic_timing={}, beat_resolution={})".format(
            self.is_symbolic_timing, self.beat_resolution
        )


class Note:
    """
    A container for note.

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

    def __init__(self, start, end, pitch, velocity):
        self.start = start
        self.end = end
        self.pitch = pitch
        self.velocity = velocity

    def __repr__(self):
        return "Note(start={:f}, end={:f}, pitch={}, velocity={})".format(
            self.start, self.end, self.pitch, self.velocity
        )

    @property
    def duration(self):
        """Duration of the note."""
        return self.end - self.start


class Annotation:
    """
    A container for annotation.

    Attributes
    ----------
    time : float
        Start time of the note, in time steps or seconds (see Note).
    annotation : str
        Annotation of any type.

    Note
    ----
    The timing unit is determined by higher-level objects.

    """

    def __init__(self, time, annotation):
        self.time = time
        self.data = annotation

    def __repr__(self):
        return "Annotation(time={:f}, annotation={})".format(self.time, self.data)


class Lyric(Annotation):
    """A container for lyric."""

    def __init__(self, time, lyric):
        if not isinstance(lyric, str):
            raise TypeError(
                "Expect `lyric` of str type, but got {}.".format(type(lyric))
            )
        super().__init__(time, lyric)


class TimeSignature:
    """
    A container for time signature.

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

    def __init__(self, time, numerator, denominator):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

    def __repr__(self):
        return "TimeSignature(time={:f}, numerator={}, denominator={})".format(
            self.time, self.numerator, self.denominator
        )


class KeySignature:
    """
    A container for key signature.

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

    def __init__(self, time, root, mode):
        self.time = time
        self.root = root
        self.mode = mode

    def __repr__(self):
        return "TimeSignature(time={:f}, root={}, mode={})".format(
            self.time, self.root, self.mode
        )


class Tempo:
    """
    A container for key signature.

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

    def __init__(self, time, tempo):
        self.time = time
        self.tempo = tempo

    def __repr__(self):
        return "Tempo(time={:f}, tempo={:f})".format(self.time, self.tempo)


class Track:
    """
    A container for music track.

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
    """

    def __init__(
        self, name="unknown", program=0, is_drum=False, notes=None, annotations=None
    ):
        self.notes = notes if notes is not None else []
        self.annotations = annotations if annotations is not None else []
        self.program = program
        self.is_drum = is_drum
        self.name = name

    def __repr__(self):
        return "Track(name={}, program={}, is_drum={}, notes={})".format(
            self.name, self.program, self.is_drum, self.notes
        )

    def append(self, obj):
        """Append a note or an annotation."""
        if isinstance(obj, Note):
            self.notes.append(obj)
        elif isinstance(obj, Annotation):
            self.annotations.append(obj)
        else:
            raise TypeError(
                "Expect Note or Annotation object, but got {}.".format(type(obj))
            )

    def sort(self):
        """Sort the notes and annotations with respect to event time."""
        self.notes.sort(key=lambda x: x.start)
        self.annotations.sort(key=lambda x: x.time)
