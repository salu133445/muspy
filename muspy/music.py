"""Core music object."""
from pathlib import Path
from typing import Union

from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .classes import Base, MetaData, TimingInfo
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
)
from .utils import append, sort


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
        append(self, obj)

    def sort(self):
        """Sort the time-stamped objects with respect to event time.

        Refer to :meth:`muspy.sort`: for full documentation.

        See Also
        --------
        :meth:`muspy.sort`: equivalent function

        """
        sort(self)

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

    def to(self, target):
        """Convert to a target representation or .

        Parameters
        ----------
        target : str
            Target representation. Supported values are 'event', 'note',
            'pianoroll', 'pretty_midi', 'pypianoroll'.

        """
        if target.lower() in ("event", "event-based"):
            return to_event_representation(self)
        if target.lower() in ("note", "note-based"):
            return to_note_representation(self)
        if target.lower() in ("pianoroll"):
            return to_pianoroll_representation(self)
        if target.lower() in ("pretty_midi"):
            return to_pretty_midi(self)
        if target.lower() in ("pypianoroll"):
            return to_pypianoroll(self)
        raise ValueError(
            "Unsupported target representation : {}.".format(target)
        )

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
