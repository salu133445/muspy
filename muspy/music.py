"""Core MusPy music object."""

import json
import os.path
from collections import OrderedDict

import jsonschema
import pretty_midi
import yamale
import yaml

import muspy.io
from muspy.classes import (
    Annotation,
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


def ordered_dump(data, stream=None, dumper=yaml.Dumper, **kwargs):
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """

    class OrderedDumper(dumper):
        """A dumper that supports OrderedDict."""

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
        )

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwargs)


class Music:
    """A universal container for music data.

    Attributes
    ----------
    is_symbolic_timing : bool
        A boolean indicating if it is in symbolic timing. Defaults to True.
    beat_resolution : list of Note
        Time steps per beat (only effective when `is_symbolic_timing` is true).
    annotations : list of :class:'muspy.Annotation'
        A list of :class:'muspy.Annotation' object.
    """

    def __init__(
        self,
        obj=None,
        tracks=None,
        metadata=None,
        timing_info=None,
        time_signatures=None,
        key_signatures=None,
        tempos=None,
        downbeats=None,
        lyrics=None,
        annotations=None,
    ):
        if obj is not None:
            if obj.endswith((".midi", ".mid", ".mxml", ".xml")):
                self.parse(obj)
            elif obj.endswith((".json", ".yaml", ".yml")):
                self.load(obj)
            else:
                raise TypeError("Expect a file or a parsable object.")
            return

        self.metadata = metadata if metadata is not None else []
        self.timing = timing_info if timing_info is not None else []
        self.time_signatures = time_signatures if time_signatures is not None else []
        self.key_signatures = key_signatures if key_signatures is not None else []
        self.tempos = tempos if tempos is not None else []
        self.downbeats = downbeats if downbeats is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []
        self.tracks = tracks if tracks is not None else []

    def reset(self):
        """Reset the object."""
        self.metadata = MetaData()
        self.timing = TimingInfo()
        self.time_signatures = []
        self.key_signatures = []
        self.tempos = []
        self.lyrics = []
        self.annotations = []
        self.tracks = []

    def parse(self, obj):
        """Load from a file or a parsable object."""
        if isinstance(obj, str):
            if obj.endswith((".mid", ".midi")):
                muspy.io.midi.parse_midi(self, obj)
            elif obj.endswith((".mxml", ".xml")):
                muspy.io.musicxml.parse_musicxml(self, obj)
            else:
                raise TypeError("Unrecognized extension (expect MIDI or MusicXML).")
        elif isinstance(obj, pretty_midi.PrettyMIDI):
            muspy.io.midi.parse_pretty_midi(self, obj)
        else:
            raise TypeError(
                "Expect a file or a parsable object, but got {}.".format(type(obj))
            )

    def load(self, filename):
        """Load from a file."""
        if filename.endswith(".json"):
            with open("muspy/schemas/music.schema.json") as in_file:
                schema = json.load(in_file)
            with open(filename) as in_file:
                data = json.load(in_file)
            jsonschema.validate(data, schema)

        elif filename.endswith((".yaml", ".yml")):
            schema = yamale.make_schema("muspy/schemas/music.schema.yaml")
            data = yamale.make_data(filename)
            yamale.validate(schema, data)
            with open(filename) as in_file:
                data = yaml.safe_load(in_file)
        else:
            raise TypeError("Unrecognized extension (expect JSON or YAML).")

        self.reset()

        # Meta data
        song_info = SongInfo(
            data["meta"]["song"]["title"],
            data["meta"]["song"]["artist"],
            data["meta"]["song"]["composers"],
        )
        source_info = SourceInfo(
            data["meta"]["source"]["id"],
            data["meta"]["source"]["collection"],
            data["meta"]["source"]["filename"],
            data["meta"]["source"]["format"],
        )
        self.metadata = MetaData(data["meta"]["schema_version"], song_info, source_info)

        # Global data
        self.timing = TimingInfo(
            data["global"]["timing"]["is_symbolic_timing"],
            data["global"]["timing"]["beat_resolution"],
        )

        if data["global"]["time_signatures"] is not None:
            for time_signature in data["global"]["time_signatures"]:
                self.time_signatures.append(
                    TimeSignature(
                        time_signature["time"],
                        time_signature["numerator"],
                        time_signature["denominator"],
                    )
                )

        if data["global"]["key_signatures"] is not None:
            for key_signature in data["global"]["key_signatures"]:
                self.key_signatures.append(
                    KeySignature(
                        key_signature["time"],
                        key_signature["root"],
                        key_signature["mode"],
                    )
                )

        if data["global"]["tempos"] is not None:
            for tempo in data["global"]["tempos"]:
                self.tempos.append(Tempo(tempo["time"], tempo["tempo"]))

        if data["global"]["downbeats"] is not None:
            self.downbeats = data["global"]["downbeats"]

        if data["global"]["lyrics"] is not None:
            for lyric in data["global"]["lyrics"]:
                self.lyrics.append(Lyric(lyric["time"], lyric["lyric"]))

        if data["global"]["annotations"] is not None:
            for annotation in data["global"]["annotations"]:
                self.annotations.append(
                    Annotation(annotation["time"], annotation["annotation"])
                )

        # Track-specific data
        self.tracks = []
        if data["tracks"] is not None:
            for track in data["tracks"]:
                notes, annotations = [], []
                for note in track["notes"]:
                    notes.append(
                        Note(
                            note["start"], note["end"], note["pitch"], note["velocity"]
                        )
                    )
                for annotation in track["annotations"]:
                    annotations.append(
                        Annotation(annotation["time"], annotation["annotation"])
                    )
                self.tracks.append(
                    Track(
                        track["name"],
                        track["program"],
                        track["is_drum"],
                        notes,
                        annotations,
                    )
                )

    def to_dict(self):
        """Convert the music object into a dictionary."""
        data = OrderedDict(
            [("meta", OrderedDict()), ("global", OrderedDict()), ("tracks", [])]
        )

        # Meta data
        data["meta"]["schema_version"] = self.metadata.schema_version

        data["meta"]["song"] = OrderedDict(
            [
                ("title", self.metadata.song.title),
                ("artist", self.metadata.song.artist),
                ("composers", self.metadata.song.composers),
            ]
        )

        data["meta"]["source"] = OrderedDict(
            [
                ("id", self.metadata.source.id),
                ("collection", self.metadata.source.collection),
                ("filename", self.metadata.source.filename),
                ("format", self.metadata.source.format),
            ]
        )

        # Global data
        data["global"]["timing"] = OrderedDict(
            [
                ("is_symbolic_timing", self.timing.is_symbolic_timing),
                ("beat_resolution", self.timing.beat_resolution),
            ]
        )

        data["global"]["time_signatures"] = []
        for time_signature in self.time_signatures:
            data["global"]["time_signatures"].append(
                OrderedDict(
                    [
                        ("time", time_signature.time),
                        ("numerator", time_signature.numerator),
                        ("denominator", time_signature.denominator),
                    ]
                )
            )

        data["global"]["key_signatures"] = []
        for key_signature in self.key_signatures:
            data["global"]["key_signatures"].append(
                OrderedDict(
                    [
                        ("time", key_signature.time),
                        ("root", key_signature.root),
                        ("mode", key_signature.mode),
                    ]
                )
            )

        data["global"]["tempos"] = []
        for tempo in self.tempos:
            data["global"]["tempos"].append(
                OrderedDict([("time", tempo.time), ("tempo", tempo.tempo)])
            )

        data["global"]["downbeats"] = self.downbeats

        data["global"]["lyrics"] = []
        for lyric in self.lyrics:
            data["global"]["lyrics"].append(
                OrderedDict([("time", lyric.time), ("lyric", lyric.data)])
            )

        data["global"]["annotations"] = []
        for annotation in self.annotations:
            data["global"]["annotations"].append(
                OrderedDict(
                    [("time", annotation.time), ("annotation", annotation.data)]
                )
            )

        # Track-specific data
        for track in self.tracks:
            notes, annotations = [], []
            for note in track.notes:
                notes.append(
                    OrderedDict(
                        [
                            ("start", note.start),
                            ("end", note.end),
                            ("pitch", note.pitch),
                            ("velocity", note.velocity),
                        ]
                    )
                )
            for annotation in track.annotations:
                annotations.append(
                    OrderedDict(
                        [("time", annotation.time), ("annotation", annotation.data)]
                    )
                )
            data["tracks"].append(
                OrderedDict(
                    [
                        ("name", track.name),
                        ("program", track.program),
                        ("is_drum", track.is_drum),
                        ("notes", notes),
                        ("annotations", annotations),
                    ]
                )
            )

        return data

    def serialize(self, format_="json"):
        """Serialize to JSON or YAML string."""
        if format_ == "json":
            return json.dumps(self.to_dict())
        if format_ == "yaml":
            return ordered_dump(self.to_dict(), Dumper=yaml.SafeDumper)
        raise ValueError("`format_` should be either 'json' or 'yaml'.")

    def save(self, filename):
        """Save to a file."""
        ext = os.path.splitext(filename.lower())[1]
        if not ext:
            raise ValueError("Filename must have an extension.")
        with open(filename, "w") as out_file:
            out_file.write(self.serialize(ext[1:]))
