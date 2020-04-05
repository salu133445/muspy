"""Core MusPy music object."""
import json
import os.path
from collections import OrderedDict

import jsonschema
import pretty_midi
import yamale
import yaml

from .classes import (
    Annotation,
    Base,
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SongInfo,
    SourceInfo,
    Tempo,
    TimeSignature,
    TimingInfo,
    Track,
)
from .io import (
    parse_pretty_midi,
    read_midi,
    read_musicxml,
    to_pretty_midi,
    to_pypianoroll,
    write_midi,
    write_musicxml,
)
from .representations import (
    to_event_representation,
    to_note_representation,
    to_pianoroll_representation,
)


class OrderedDumper(yaml.SafeDumper):
    """A dumper that supports OrderedDict."""

    def increase_indent(self, flow=False, indentless=False):
        return super(OrderedDumper, self).increase_indent(flow, False)


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


OrderedDumper.add_representer(OrderedDict, _dict_representer)


def ordered_dump(data):
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """
    return yaml.dump(data, Dumper=OrderedDumper)


class Music(Base):
    """A universal container for music data.

    Attributes
    ----------
    timing : :class:muspy.TimingInfo object
        A timing info object. See :class:`muspy.TimingInfo` for details.
    time_signatures : list of :class:`muspy.TimeSignature` object
        Time signatures. See :class:`muspy.TimeSignature` for details.
    key_signatures : list of :class:`muspy.KeySignature` object
        Time signatures. See :class:`muspy.KeySignature` for details.
    tempos : list of :class:muspy.Tempo object
        Tempos. See :class:`muspy.Tempo` for details.
    downbeats : list of float
        Downbeat positions.
    lyrics : list of :class:`muspy.Lyric`
        Lyrics. See :class:`muspy.Lyric` for details.
    annotations : list of :class:`muspy.Annotation`
        Annotations. See :class:`muspy.Annotation` for details.
    tracks : list of :class:`muspy.Track`
        Music tracks. See :class:`muspy.Track` for details.
    meta : :class:`muspy.MetaData` object
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
        "meta",
    ]

    def __init__(
        self,
        obj=None,
        meta_data=None,
        timing_info=None,
        time_signatures=None,
        key_signatures=None,
        tempos=None,
        downbeats=None,
        lyrics=None,
        annotations=None,
        tracks=None,
    ):
        if obj is not None:
            if obj.endswith((".midi", ".mid", ".mxml", ".xml")):
                self.parse(obj)
            elif obj.endswith((".json", ".yaml", ".yml")):
                self.load(obj)
            else:
                raise TypeError("Expect a file or a parsable object.")
            return

        self.timing = timing_info if timing_info is not None else []
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
        self.meta = meta_data if meta_data is not None else []

    def reset(self):
        """Reset the object."""
        self.timing = TimingInfo()
        self.time_signatures = []
        self.key_signatures = []
        self.tempos = []
        self.lyrics = []
        self.annotations = []
        self.tracks = []
        self.meta = MetaData()

    def parse(self, obj):
        """Load from a file or a parsable object.

        Parameters
        ----------
        obj : str or :class:`pretty_midi.PrettyMIDI` object
            Path to the file to parse or the object to parse.
        """
        if isinstance(obj, str):
            if obj.lower().endswith((".mid", ".midi")):
                read_midi(self, obj)
            elif obj.lower().endswith((".mxml", ".xml")):
                read_musicxml(self, obj)
            else:
                raise TypeError(
                    "Unrecognized extension (expect MIDI or MusicXML)."
                )
        elif isinstance(obj, pretty_midi.PrettyMIDI):
            parse_pretty_midi(self, obj)
        else:
            raise TypeError(
                "Expect a file or a parsable object, but got {}.".format(
                    type(obj)
                )
            )

    def load(self, filename):
        """Load from a file.

        Parameters
        ----------
        filename : str
            Path to the file to load.
        """
        if filename.lower().endswith(".json"):
            with open("muspy/schemas/music.schema.json") as f:
                schema = json.load(f)
            with open(filename) as f:
                data = json.load(f)
            jsonschema.validate(data, schema)

        elif filename.lower().endswith((".yaml", ".yml")):
            schema = yamale.make_schema("muspy/schemas/music.schema.yaml")
            data = yamale.make_data(filename)
            yamale.validate(schema, data)
            with open(filename) as f:
                data = yaml.safe_load(f)
        else:
            raise TypeError("Unrecognized extension (expect JSON or YAML).")

        self.reset()

        # Global data
        self.timing = TimingInfo(
            data["timing"]["is_symbolic_timing"],
            data["timing"]["beat_resolution"],
        )

        if data["time_signatures"] is not None:
            for time_signature in data["time_signatures"]:
                self.time_signatures.append(
                    TimeSignature(
                        time_signature["time"],
                        time_signature["numerator"],
                        time_signature["denominator"],
                    )
                )

        if data["key_signatures"] is not None:
            for key_signature in data["key_signatures"]:
                self.key_signatures.append(
                    KeySignature(
                        key_signature["time"],
                        key_signature["root"],
                        key_signature["mode"],
                    )
                )

        if data["tempos"] is not None:
            for tempo in data["tempos"]:
                self.tempos.append(Tempo(tempo["time"], tempo["tempo"]))

        if data["downbeats"] is not None:
            self.downbeats = data["downbeats"]

        if data["lyrics"] is not None:
            for lyric in data["lyrics"]:
                self.lyrics.append(Lyric(lyric["time"], lyric["lyric"]))

        if data["annotations"] is not None:
            for annotation in data["annotations"]:
                self.annotations.append(
                    Annotation(annotation["time"], annotation["annotation"])
                )

        # Track-specific data
        self.tracks = []
        if data["tracks"] is not None:
            for track in data["tracks"]:
                notes, annotations, lyrics = [], [], []
                for note in track["notes"]:
                    notes.append(
                        Note(
                            note["start"],
                            note["end"],
                            note["pitch"],
                            note["velocity"],
                        )
                    )
                for annotation in track["annotations"]:
                    annotations.append(
                        Annotation(
                            annotation["time"], annotation["annotation"]
                        )
                    )
                for lyric in track["lyrics"]:
                    lyrics.append(Annotation(lyric["time"], lyric["lyric"]))
                self.tracks.append(
                    Track(
                        track["name"],
                        track["program"],
                        track["is_drum"],
                        notes,
                        annotations,
                        lyrics,
                    )
                )

        # Meta data
        song_info = SongInfo(
            data["meta"]["song"]["title"],
            data["meta"]["song"]["artist"],
            data["meta"]["song"]["composers"],
        )
        source_info = SourceInfo(
            data["meta"]["source"]["collection"],
            data["meta"]["source"]["filename"],
            data["meta"]["source"]["format"],
            data["meta"]["source"]["id"],
        )
        self.meta = MetaData(
            data["meta"]["schema_version"], song_info, source_info
        )

    def serialize(self, format_="json"):
        """Serialize to JSON or YAML string.

        Parameters
        ----------
        format_ : {'json', 'yaml'}, optional
            Target file format. Defaults to 'json'.
        """
        if format_.lower() == "json":
            return json.dumps(self.to_ordered_dict())
        if format_.lower() in ("yaml", "yml"):
            return ordered_dump(self.to_ordered_dict())
        raise ValueError("`format_` should be either 'json' or 'yaml'.")

    def save(self, filename):
        """Save to a file.

        Parameters
        ----------
        filename : str
            Path to save the file. Supported extensions are `.json` and `.yaml`.

        Note
        ----
        To write to other formats such as MIDI or MusicXML, see
        :meth:`muspy.Music.write`.
        """
        ext = os.path.splitext(filename)[1]
        if not ext:
            raise ValueError("Filename must have an extension.")
        with open(filename, "w") as out_file:
            out_file.write(self.serialize(ext[1:]))

    def write(self, filename):
        """Write to a file in a specific format.

        Parameters
        ----------
        filename : str
            Path to write the file. Supported extensions are `.mxml` and `.mid`.
        """
        ext = os.path.splitext(filename)[1]
        if not ext:
            raise ValueError("Filename must have an extension.")
        if ext.lower() == ".mxml":
            return write_musicxml(self, filename)
        if ext.lower() in (".midi", ".mid"):
            return write_midi(self, filename)
        raise ValueError("Unsupported file extension : {}.".format(ext))

    def to(self, target):
        """Convert to a target representation.

        Parameters
        ----------
        target : str
            Target representation. Supported values are 'event', 'note',
            'pianoroll', 'pretty_midi', 'pypianoroll'.
        """
        if target.lower() in ("event", "event-based"):
            return self.to_event_representation()
        if target.lower() in ("note", "note-based"):
            return self.to_note_representation()
        if target.lower() in ("pianoroll"):
            return self.to_pianoroll_representation()
        if target.lower() in ("pretty_midi"):
            return self.to_pretty_midi()
        if target.lower() in ("pypianoroll"):
            return self.to_pypianoroll()
        raise ValueError(
            "Unsupported target representation : {}.".format(target)
        )

    def to_event_representation(self):
        """Convert to event-based representation."""
        to_event_representation(self)

    def to_note_representation(self):
        """Convert to note-based representation."""
        to_note_representation(self)

    def to_pianoroll_representation(self):
        """Convert to pianoroll representation."""
        to_pianoroll_representation(self)

    def to_pretty_midi(self):
        """Convert to a :class:`pretty_midi.PrettyMIDI` object."""
        to_pretty_midi(self)

    def to_pypianoroll(self):
        """Convert to a :class:`pypianoroll.Multitrack` object."""
        to_pypianoroll(self)
