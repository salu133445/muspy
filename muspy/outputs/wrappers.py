"""Wrapper functions for output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, TextIO, Union

from mido import MidiFile
from music21.stream import Stream
from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .abc import write_abc
from .audio import write_audio
from .event import to_event_representation
from .json import save_json
from .midi import to_mido, to_pretty_midi, write_midi
from .music21 import to_music21
from .musicxml import write_musicxml
from .note import to_note_representation
from .pianoroll import to_pianoroll_representation, to_pypianoroll
from .pitch import to_pitch_representation
from .yaml import save_yaml

if TYPE_CHECKING:
    from ..music import Music


def save(
    path: Union[str, Path, TextIO], music: "Music", kind: str = None, **kwargs,
):
    """Save a Music object loselessly to a JSON or a YAML file.

    This is a wrapper function for :func:`muspy.save_json` and
    :func:`muspy.save_yaml`.

    Parameters
    ----------
    path : str, Path or TextIO
        Path or file to save the data.
    music : :class:`muspy.Music`
        Music object to save.
    kind : {'json', 'yaml'}, optional
        Format to save. Defaults to infer from the extension.
    **kwargs
        Keyword arguments to pass to :func:`muspy.save_json` or
        :func:`muspy.save_yaml`.

    See Also
    --------
    :func:`muspy.save_json` : Save a Music object to a JSON file.
    :func:`muspy.save_yaml` : Save a Music object to a YAML file.
    :func:`muspy.write` :
        Write a Music object to a MIDI/MusicXML/ABC/audio file.

    Notes
    -----
    The conversion can be lossy if any nonserializable object is used
    (for example, an Annotation object, which can store data of any
    type).

    """
    if kind is None:
        if not isinstance(path, (str, Path)):
            raise ValueError("Cannot infer file format from a file object.")
        path_str = str(path).lower()
        if path_str.endswith((".json", ".json.gz")):
            kind = "json"
        elif path_str.endswith((".yaml", ".yml", ".yaml.gz", ".yml.gz")):
            kind = "yaml"
        else:
            raise ValueError(
                "Cannot infer file format from the extension (expect JSON or "
                "YAML)."
            )
    if kind.lower() == "json":
        return save_json(path, music, **kwargs)
    if kind.lower() == "yaml":
        return save_yaml(path, music, **kwargs)
    raise ValueError(
        f"Expect `kind` to be 'json' or 'yaml', but got : {kind}."
    )


def write(
    path: Union[str, Path], music: "Music", kind: str = None, **kwargs,
):
    """Write a Music object to a MIDI/MusicXML/ABC/audio file.

    Parameters
    ----------
    path : str or Path
        Path to write the file.
    music : :class:`muspy.Music`
        Music object to convert.
    kind : {'midi', 'musicxml', 'abc', 'audio'}, optional
        Format to save. Defaults to infer from the extension.

    See Also
    --------
    :func:`muspy.save` :
        Save a Music object loselessly to a JSON or a YAML file.

    """
    if kind is None:
        if str(path).lower().endswith((".mid", ".midi")):
            kind = "midi"
        elif (
            str(path).lower().endswith((".mxl", ".xml", ".mxml", ".musicxml"))
        ):
            kind = "musicxml"
        elif str(path).lower().endswith(".abc"):
            kind = "abc"
        elif str(path).lower().endswith(("wav", "aiff", "flac", "oga")):
            kind = "audio"
        else:
            raise ValueError(
                "Cannot infer file format from the extension (expect MIDI, "
                "MusicXML, ABC, WAV, AIFF, FLAC or OGA)."
            )
    if kind.lower() == "midi":
        return write_midi(path, music, **kwargs)
    if kind.lower() == "musicxml":
        return write_musicxml(path, music, **kwargs)
    if kind.lower() == "abc":
        return write_abc(path, music, **kwargs)
    if kind.lower() == "audio":
        return write_audio(path, music, **kwargs)
    raise ValueError(
        "Expect `kind` to be 'midi', 'musicxml', 'abc' or 'audio', but"
        f"got : {kind}."
    )


def to_object(
    music: "Music", kind: str, **kwargs
) -> Union[Stream, MidiFile, PrettyMIDI, Multitrack]:
    """Return a Music object as an object in other libraries.

    Supported classes are `music21.Stream`, :class:`mido.MidiTrack`,
    :class:`pretty_midi.PrettyMIDI` and :class:`pypianoroll.Multitrack`.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to convert.
    kind : str, {'music21', 'mido', 'pretty_midi', 'pypianoroll'}
        Target class.

    Returns
    -------
    `music21.Stream`, :class:`mido.MidiTrack`, \
            :class:`pretty_midi.PrettyMIDI` or \
            :class:`pypianoroll.Multitrack`
        Converted object.

    """
    if kind.lower() == "music21":
        return to_music21(music)
    if kind.lower() == "mido":
        return to_mido(music, **kwargs)
    if kind.lower() in ("pretty_midi", "prettymidi", "pretty-midi"):
        return to_pretty_midi(music)
    if kind.lower() == "pypianoroll":
        return to_pypianoroll(music)
    raise ValueError(
        "Expect `kind` to be 'music21', 'mido', 'pretty_midi' or "
        f"'pypianoroll', but got : {kind}."
    )


def to_representation(music: "Music", kind: str, **kwargs) -> ndarray:
    """Return a Music object in a specific representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to convert.
    kind : str, {'pitch', 'piano-roll', 'event', 'note'}
        Target representation.

    Returns
    -------
    array : ndarray
        Converted representation.

    """
    if kind.lower() in ("pitch", "pitch-based"):
        return to_pitch_representation(music, **kwargs)
    if kind.lower() in ("piano-roll", "pianoroll", "piano roll"):
        return to_pianoroll_representation(music, **kwargs)
    if kind.lower() in ("event", "event-based"):
        return to_event_representation(music, **kwargs)
    if kind.lower() in ("note", "note-based"):
        return to_note_representation(music, **kwargs)
    raise ValueError(
        "Expect `kind` to be 'pitch', 'pianoroll', 'event' or 'note', but"
        f"got : {kind}."
    )
