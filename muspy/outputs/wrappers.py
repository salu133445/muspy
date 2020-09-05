"""Wrapper functions for output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

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
    path: Union[str, Path],
    music: "Music",
    kind: Optional[str] = None,
    **kwargs: Any
):
    """Save a Music object loselessly to a JSON or a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to save the file.
    music : :class:`muspy.Music` object
        Music object to save.
    kind : {'json', 'yaml'}, optional
        Format to save (case-insensitive). Defaults to infer the format from
        the extension.

    See Also
    --------
    :func:`muspy.write` : Write to other formats such as MIDI and MusicXML.

    Notes
    -----
    The conversion can be lossy if any nonserializable object is used (for
    example, in an Annotation object, which can store data of any type).

    """
    if kind is None:
        if str(path).lower().endswith(".json"):
            kind = "json"
        elif str(path).lower().endswith((".yaml", ".yml")):
            kind = "yaml"
        else:
            raise ValueError(
                "Got unsupported file format (expect JSON or YAML)."
            )
    if kind == "json":
        return save_json(path, music, **kwargs)  # type: ignore
    if kind == "yaml":
        return save_yaml(path, music, **kwargs)  # type: ignore
    raise ValueError("`kind` must be either 'json' or 'yaml'.")


def write(
    path: Union[str, Path],
    music: "Music",
    kind: Optional[str] = None,
    **kwargs: Any
):
    """Write a Music object to a MIDI, a MusicXML, an ABC or an audio file.

    Parameters
    ----------
    path : str or Path
        Path to write the file.
    music : :class:`muspy.Music` object
        Music object to convert.
    kind : {'midi', 'musicxml', 'abc', 'audio'}, optional
        Format to save (case-insensitive). Defaults to infer the format from
        the extension.

    See Also
    --------
    :func:`muspy.save` : Losslessly save to a JSON or a YAML file.

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
                "Got unsupported file format (expect MIDI, MusicXML, ABC, "
                "WAV, AIFF, FLAC or OGA)."
            )
    if kind == "midi":
        return write_midi(path, music, **kwargs)
    if kind == "musicxml":
        return write_musicxml(path, music, **kwargs)
    if kind == "abc":
        return write_abc(path, music)
    if kind == "audio":
        return write_audio(path, music, **kwargs)
    raise ValueError("`kind` must be 'midi', 'musicxml', 'abc' or 'audio'.")


def to_object(
    music: "Music", target: str, **kwargs: Any
) -> Union[Stream, MidiFile, PrettyMIDI, Multitrack]:
    """Return a Music object as a PrettyMIDI or a Multitrack object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    target : str, {'music21', 'mido', 'pretty_midi', 'pypianoroll'}
        Target class (case-insensitive).

    Returns
    -------
    `music21.Stream` or :class:`mido.MidiTrack` or
    :class:`pretty_midi.PrettyMIDI` or :class:`pypianoroll.Multitrack`
    object
        Converted object.

    """
    if target.lower() == "music21":
        return to_music21(music)
    if target.lower() == "mido":
        return to_mido(music, **kwargs)
    if target.lower() in ("pretty_midi", "prettymidi", "pretty-midi"):
        return to_pretty_midi(music)
    if target.lower() == "pypianoroll":
        return to_pypianoroll(music)
    raise ValueError(
        "`target` must be one of 'music21', 'mido', 'pretty_midi' and "
        "'pypianoroll'."
    )


def to_representation(music: "Music", kind: str, **kwargs: Any) -> ndarray:
    """Return a Music object in a specific representation.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    kind : str, {'pitch', 'piano-roll', 'event', 'note'}
        Target representation (case-insensitive).

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
        "`kind` must be one of 'pitch', 'piano-roll', 'event' and 'note'."
    )
