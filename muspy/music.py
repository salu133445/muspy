"""Core music object."""
from pathlib import Path
from typing import List, Mapping, Optional, Union

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
    remove_invalid_from_list,
    validate_list,
)
from .outputs import (
    save,
    save_json,
    save_yaml,
    to_object,
    to_pretty_midi,
    to_pypianoroll,
    write,
    write_midi,
    write_musicxml,
)
from .representations import to_representation

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
        "meta_data",
        "timing",
        "time_signatures",
        "key_signatures",
        "tempos",
        "downbeats",
        "lyrics",
        "annotations",
        "tracks",
    ]

    def __init__(
        self,
        meta_data: Optional[MetaData] = None,
        timing_info: Optional[TimingInfo] = None,
        time_signatures: Optional[List[TimeSignature]] = None,
        key_signatures: Optional[List[KeySignature]] = None,
        tempos: Optional[List[Tempo]] = None,
        downbeats: Optional[List[Union[int, float]]] = None,
        lyrics: Optional[List[Lyric]] = None,
        annotations: Optional[List[Annotation]] = None,
        tracks: Optional[List[Track]] = None,
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

    @classmethod
    def from_dict(cls, dict_: Mapping) -> "Music":
        """Return an instance constructed from a dictionary.

        Parameters
        ----------
        dict_ : dict
            A dictionary that stores the attributes and their values as
            key-value pairs.

        """
        # Meta data
        meta_data = MetaData.from_dict(dict_["meta"])

        # Global data
        timing = TimingInfo.from_dict(dict_["timing"])

        if dict_["time_signatures"] is not None:
            time_signatures = [
                TimeSignature.from_dict(time_signature)
                for time_signature in dict_["time_signatures"]
            ]

        if dict_["key_signatures"] is not None:
            key_signatures = [
                KeySignature.from_dict(key_signature)
                for key_signature in dict_["key_signatures"]
            ]

        if dict_["tempos"] is not None:
            tempos = [Tempo.from_dict(tempo) for tempo in dict_["tempos"]]

        if dict_["downbeats"] is not None:
            downbeats = dict_["downbeats"]

        if dict_["lyrics"] is not None:
            lyrics = [Lyric.from_dict(lyric) for lyric in dict_["lyrics"]]

        if dict_["annotations"] is not None:
            annotations = [
                Annotation.from_dict(annotation)
                for annotation in dict_["annotations"]
            ]

        # Track-specific data
        if dict_["tracks"] is not None:
            tracks = [Track.from_dict(track) for track in dict_["tracks"]]

        return cls(
            meta_data,
            timing,
            time_signatures,
            key_signatures,
            tempos,
            downbeats,
            lyrics,
            annotations,
            tracks,
        )

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
            raise TypeError("`meta_data` must be of type MetaData.")
        if not isinstance(self.timing, TimingInfo):
            raise TypeError("`timing` must be of type TimingInfo.")
        self.meta_data.validate()
        self.timing.validate()
        validate_list(self.time_signatures)
        validate_list(self.key_signatures)
        validate_list(self.tempos)
        validate_list(self.lyrics)
        validate_list(self.annotations)
        validate_list(self.tracks)

    def remove_invalid(self):
        """Remove invalid objects.

        This includes time signatures, key signatures, tempos, lyrics and
        annotations, along with notes, lyrics and annotations for each track.

        """
        self.time_signatures = remove_invalid_from_list(self.time_signatures)
        self.key_signatures = remove_invalid_from_list(self.key_signatures)
        self.tempos = remove_invalid_from_list(self.tempos)
        self.lyrics = remove_invalid_from_list(self.lyrics)
        self.annotations = remove_invalid_from_list(self.annotations)
        for track in self.tracks:
            track.remove_invalid()

    def get_active_length(self, is_sorted=False) -> Union[int, float]:
        """Return the end time of the last note in all tracks."""
        return max(
            [track.get_active_length(is_sorted) for track in self.tracks]
        )

    def get_length(self, is_sorted=False) -> Union[int, float]:
        """Return the time of the last event in all tracks.

        This includes time signatures, key signatures, tempos notes onsets,
        note offsets, lyrics and annotations.

        """
        if is_sorted:
            return max(
                self.get_active_length(is_sorted),
                self.time_signatures[-1].time,
                self.key_signatures[-1].time,
                self.tempos[-1].time,
                self.lyrics[-1].time,
                self.annotations[-1].time,
            )
        return max(
            self.get_active_length(is_sorted),
            max([time_sign.time for time_sign in self.time_signatures]),
            max([key_sign.time for key_sign in self.key_signatures]),
            max([tempo.time for tempo in self.tempos]),
            max([lyric.time for lyric in self.lyrics]),
            max([annotation.time for annotation in self.annotations]),
        )

    def append(self, obj):
        """Append an object to the correseponding list.

        Parameters
        ----------
        obj : Muspy objects (see below)
            Object to be appended. Supported object types are
            :class:`muspy.TimeSignature`, :class:`muspy.KeySignature`,
            :class:`muspy.Tempo`, :class:`muspy.Lyric`,
            :class:`muspy.Annotation` and :class:`muspy.Track` objects.

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

        Refer to :func:`muspy.sort`: for full documentation.

        See Also
        --------
        :func:`muspy.sort`: equivalent function

        """
        self.time_signatures.sort(key=lambda x: x.start)
        self.key_signatures.sort(key=lambda x: x.time)
        self.tempos.sort(key=lambda x: x.time)
        self.lyrics.sort(key=lambda x: x.time)
        self.annotations.sort(key=lambda x: x.time)
        for track in self.tracks:
            track.sort()

    def transpose(self, semitone: int):
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

        Refer to :func:`muspy.io.save`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to save the file. The file format is inferred from the
            extension.

        See Also
        --------
        :func:`muspy.io.save`: equivalent function
        :func:`muspy.io.write`: write to other formats such as MIDI and MusicXML

        """
        save(self, path)

    def save_json(self, path: Union[str, Path]):
        """Save loselessly to a JSON file.

        Refer to :func:`muspy.io.save_json`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to save the JSON file.

        See Also
        --------
        :func:`muspy.io.save_json`: equivalent function

        """
        save_json(self, path)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :func:`muspy.io.save_yaml`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to save the YAML file.

        See Also
        --------
        :func:`muspy.io.save_yaml`: equivalent function

        """
        save_yaml(self, path)

    def write(self, path: Union[str, Path]):
        """Write to a MIDI or a MusicXML file.

        Refer to :func:`muspy.io.write`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to write the file. The file format is inferred from the
            extension.

        See Also
        --------
        :func:`muspy.io.write`: equivalent function
        :func:`muspy.io.save`: losslessly save to a JSON and a YAML file

        """
        write(self, path)

    def write_midi(self, path: Union[str, Path]):
        """Write to a MIDI file.

        Refer to :func:`muspy.io.write_midi`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to write the MIDI file.

        See Also
        --------
        :func:`muspy.io.write_midi(self, path)`: equivalent function

        """
        write_midi(self, path)

    def write_musicxml(self, path: Union[str, Path]):
        """Write to a MusicXML file.

        Refer to :func:`muspy.io.write_musicxml`: for full documentation.

        Parameters
        ----------
        path : str or Path
            Path to write the MusicXML file.

        See Also
        --------
        :func:`muspy.io.write_musicxml(self, path)`: equivalent function

        """
        write_musicxml(self, path)

    def to_object(self, target: str):
        """Convert to a target class.

        Parameters
        ----------
        target : str
            Target class. Supported values are 'pretty_midi' and 'pypianoroll'.

        """
        return to_object(self, target)

    def to_pretty_midi(self) -> PrettyMIDI:
        """Return as a PrettyMIDI object."""
        return to_pretty_midi(self)

    def to_pypianoroll(self) -> Multitrack:
        """Return as a Multitrack object."""
        return to_pypianoroll(self)

    def to_representation(self, target: str):
        """Convert to a target class.

        Parameters
        ----------
        target : str
            Target representation. Supported values are 'event', 'note' and
            'pianoroll'.

        """
        return to_representation(self, target)

    def to_event_representation(self):
        """Return the event-based representation."""
        to_representation(self, "event")

    def to_note_representation(self):
        """Return the note-based representation."""
        to_representation(self, "note")

    def to_pianoroll_representation(self):
        """Return the pianoroll representation."""
        to_representation(self, "pianoroll")
