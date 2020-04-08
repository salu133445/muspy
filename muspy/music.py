"""Core music object."""
from pathlib import Path
from typing import Union

from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .classes import (
    Annotation,
    Base,
    KeySignature,
    Lyric,
    MetaData,
    Tempo,
    TimeSignature,
    TimingInfo,
    Track,
)
from .io import (
    save,
    save_json,
    save_yaml,
    to_pretty_midi,
    to_pypianoroll,
    write,
    write_midi,
    write_musicxml,
)
from .representations import (
    to_event_representation,
    to_note_representation,
    to_pianoroll_representation,
    to_representation,
)
from .utils import validate_list

# pylint: disable=super-init-not-called


class Music(Base):
    """A universal container for music data.

    Attributes
    ----------
    timing : :class:`muspy.TimingInfo` object
        A timing info object. See :class:`muspy.TimingInfo` for details.
    time_signatures : list of :class:`muspy.TimeSignature` object
        Time signatures. See :class:`muspy.TimeSignature` for details.
    key_signatures : list of :class:`muspy.KeySignature` object
        Time signatures. See :class:`muspy.KeySignature` for details.
    tempos : list of :class:`muspy.Tempo` object
        Tempos. See :class:`muspy.Tempo` for details.
    downbeats : list of int or float
        Downbeat positions.
    lyrics : list of :class:`muspy.Lyric`
        Lyrics. See :class:`muspy.Lyric` for details.
    annotations : list of :class:`muspy.Annotation`
        Annotations. See :class:`muspy.Annotation` for details.
    tracks : list of :class:`muspy.Track`
        Music tracks. See :class:`muspy.Track` for details.
    meta_data : :class:`muspy.MetaData` object
        Meta data. See :class:`muspy.MetaData` for details.

    """

    _attributes = [
        "timing",
        "time_signatures",
        "key_signatures",
        "tempos",
        "downbeats",
        "lyrics",
        "annotations",
        "tracks",
        "meta_data",
    ]

    def __init__(
        self,
        timing_info=None,
        time_signatures=None,
        key_signatures=None,
        tempos=None,
        downbeats=None,
        lyrics=None,
        annotations=None,
        tracks=None,
        meta_data=None,
    ):
        self.meta_data = meta_data if meta_data is not None else MetaData()
        self.timing = timing_info if timing_info is not None else TimingInfo()
        self.time_signatures = (
            time_signatures if time_signatures is not None else []
        )
        self.key_signatures = (
            key_signatures if key_signatures is not None else []
        )
        self.tempos = tempos if tempos is not None else []
        self.downbeats = downbeats if downbeats is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []
        self.tracks = tracks if tracks is not None else []

    def reset(self):
        """Reset the object."""
        self.meta_data = MetaData()
        self.timing = TimingInfo()
        self.time_signatures = []
        self.key_signatures = []
        self.tempos = []
        self.lyrics = []
        self.annotations = []
        self.tracks = []

    def validate(self):
        """Validate the object, and raise errors for invalid attributes."""
        if not isinstance(self.meta_data, MetaData):
            return TypeError("`meta_data` must be of type MetaData.")
        if not isinstance(self.timing, TimingInfo):
            return TypeError("`timing` must be of type TimingInfo.")
        self.meta_data.validate()
        self.timing.validate()
        validate_list(self.time_signatures, "time_signatures")
        validate_list(self.key_signatures, "key_signatures")
        validate_list(self.tempos, "tempos")
        validate_list(self.lyrics, "lyrics")
        validate_list(self.annotations, "annotations")
        validate_list(self.tracks, "tracks")

    def standardize(self):
        """Standardize the object."""
        for track in self.tracks:
            track.standardize()
        self.lyrics = [
            lyric for lyric in self.lyrics if lyric.lyric and lyric.time > 0
        ]
        self.annotations = [
            annotation
            for annotation in self.annotations
            if annotation.time > 0
        ]
        # TODO: NEXT
        self.validate()

    def append(self, obj):
        """Append an object to the correseponding list.

        Parameters
        ----------
        obj : Muspy objects (see below)
            Object to be appended. Supported object types are
            :class:`Muspy.TimeSignature`, :class:`Muspy.KeySignature`,
            :class:`Muspy.Tempo`, :class:`Muspy.Lyric`,
            :class:`Muspy.Annotation` and :class:`Muspy.Track` objects.

        See Also
        --------
        :meth:`muspy.append`: equivalent function

        """
        if isinstance(obj, TimeSignature):
            self.time_signatures.append(obj)
        elif isinstance(obj, KeySignature):
            self.key_signatures.append(obj)
        elif isinstance(obj, Tempo):
            self.tempos.append(obj)
        elif isinstance(obj, Lyric):
            self.lyrics.append(obj)
        elif isinstance(obj, Annotation):
            self.annotations.append(obj)
        elif isinstance(obj, Track):
            self.tracks.append(obj)
        else:
            raise TypeError(
                "Expect TimeSignature, KeySignature, Tempo, Note, Lyric, "
                "Annotation or Track object, but got {}.".format(type(obj))
            )

    def clip(
        self, lower: Union[int, float] = 0, upper: Union[int, float] = 127
    ):
        """Clip the velocity of each note for each track.

        Parameters
        ----------
        lower : int or float, optional
            Lower bound. Defaults to 0.
        upper : int or float, optional
            Upper bound. Defaults to 127.

        """
        for track in self.tracks:
            track.clip(lower, upper)

    def sort(self):
        """Sort the time-stamped objects with respect to event time.

        Refer to :meth:`muspy.sort`: for full documentation.

        See Also
        --------
        :meth:`muspy.sort`: equivalent function

        """
        self.time_signatures.sort(key=lambda x: x.start)
        self.key_signatures.sort(key=lambda x: x.time)
        self.tempos.sort(key=lambda x: x.time)
        self.lyrics.sort(key=lambda x: x.time)
        self.annotations.sort(key=lambda x: x.time)
        for track in self.tracks:
            track.sort()

    def transpose(self, semitone):
        """Transpose all the notes for all tracks by a number of semitones.

        Parameters
        ----------
        semitone : int
            The number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the pitches.

        """
        for track in self.tracks:
            track.transpose(semitone)

    def save(self, path: Union[str, Path]):
        """Save loselessly to a JSON or a YAML file.

        Refer to :meth:`muspy.save`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to save the file. The file format is inferred from the
            extension.

        See Also
        --------
        - :meth:`muspy.save`: equivalent function
        - :meth:`muspy.write`: write to other formats such as MIDI and MusicXML

        """
        save(self, path)

    def save_json(self, path: Union[str, Path]):
        """Save loselessly to a JSON file.

        Refer to :meth:`muspy.save_json`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to save the JSON file.

        See Also
        --------
        :meth:`muspy.save_json`: equivalent function

        """
        save_json(self, path)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :meth:`muspy.save_yaml`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to save the YAML file.

        See Also
        --------
        :meth:`muspy.save_yaml`: equivalent function

        """
        save_yaml(self, path)

    def write(self, path: Union[str, Path]):
        """Write to a MIDI or a MusicXML file.

        Refer to :meth:`muspy.write`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to write the file. The file format is inferred from the
            extension.

        See Also
        --------
        - :meth:`muspy.write`: equivalent function
        - :meth:`muspy.save`: losslessly save to a JSON and a YAML file

        """
        write(self, path)

    def write_midi(self, path: Union[str, Path]):
        """Write to a MIDI file.

        Refer to :meth:`muspy.write_midi`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to write the MIDI file.

        See Also
        --------
        :class:`muspy.write_midi(self, path)`: equivalent function

        """
        write_midi(self, path)

    def write_musicxml(self, path: Union[str, Path]):
        """Write to a MusicXML file.

        Refer to :meth:`muspy.write_musicxml`: for full documentation.

        Parameters
        ----------
        path : str or :class:`pathlib.Path`
            Path to write the MusicXML file.

        See Also
        --------
        :class:`muspy.write_musicxml(self, path)`: equivalent function

        """
        write_musicxml(self, path)

    def to(self, target: str):
        """Convert to a target representation, object or dataset.

        Parameters
        ----------
        target : str
            Target representation. Supported values are 'event', 'note',
            'pianoroll', 'pretty_midi', 'pypianoroll'.

        """
        if target.lower() in (
            "event",
            "event-based",
            "note",
            "note-based",
            "pianoroll",
            "piano-roll",
        ):
            return to_representation(self, target)
        if target.lower() in ("pretty_midi"):
            return to_pretty_midi(self)
        if target.lower() in ("pypianoroll"):
            return to_pypianoroll(self)
        raise ValueError("Unsupported target : {}.".format(target))

    def to_representation(self, target: str):
        """Convert to a target representation.

        Parameters
        ----------
        target : str
            Target representation. Supported values are 'event', 'note',
            'pianoroll'.

        """
        return to_representation(self, target)

    def to_event_representation(self):
        """Return the event-based representation."""
        to_event_representation(self)

    def to_note_representation(self):
        """Return the note-based representation."""
        to_note_representation(self)

    def to_pianoroll_representation(self):
        """Return the pianoroll representation."""
        to_pianoroll_representation(self)

    def to_pretty_midi(self) -> PrettyMIDI:
        """Return as a PrettyMIDI object."""
        to_pretty_midi(self)

    def to_pypianoroll(self) -> Multitrack:
        """Return as a Multitrack object."""
        to_pypianoroll(self)
