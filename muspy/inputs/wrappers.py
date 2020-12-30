"""Wrapper functions for input interface."""
from pathlib import Path
from typing import List, Optional, Union

from mido import MidiFile
from music21.stream import Stream
from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from ..classes import Track
from ..music import Music
from .abc import read_abc
from .event import from_event_representation
from .json import load_json
from .midi import from_mido, from_pretty_midi, read_midi
from .music21 import from_music21
from .musicxml import read_musicxml
from .note import from_note_representation
from .pianoroll import from_pianoroll_representation, from_pypianoroll
from .pitch import from_pitch_representation
from .yaml import load_yaml


def load(path: Union[str, Path], kind: Optional[str] = None) -> Music:
    """Load a JSON or a YAML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the file to load.
    kind : {'json', 'yaml'}, optional
        Format to save (case-insensitive). Defaults to infer the format
        from the extension.

    Returns
    -------
    :class:`muspy.Music`
        Loaded Music object.

    See Also
    --------
    :func:`muspy.read` :
        Read a MIDI/MusicXML/ABC file into a Music object.

    """
    # pylint: disable=unused-argument
    if kind is None:
        if str(path).lower().endswith(".json"):
            kind = "json"
        elif str(path).lower().endswith((".yaml", ".yml")):
            kind = "yaml"
        else:
            raise ValueError(
                "Cannot infer file format from the extension (expect JSON or "
                "YAML)."
            )
    if kind.lower() == "json":
        return load_json(path)
    if kind.lower() == "yaml":
        return load_yaml(path)
    raise ValueError(
        f"Expect `kind` to be 'json' or 'yaml', but got : {kind}."
    )


def read(
    path: Union[str, Path], kind: Optional[str] = None, **kwargs
) -> Union[Music, List[Music]]:
    """Read a MIDI/MusicXML/ABC file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the file to read.
    kind : {'midi', 'musicxml', 'abc'}, optional
        Format to save (case-insensitive). Defaults to infer the format
        from the extension.
    **kwargs
        Keyword arguments to pass to :func:`muspy.read_midi`,
        :func:`muspy.read_musicxml` or :func:`read_abc`.

    Returns
    -------
    :class:`muspy.Music` or list of :class:`muspy.Music`
        Converted Music object(s).

    See Also
    --------
    :func:`muspy.load` : Load a JSON or a YAML file into a Music object.

    """
    if kind is None:
        if str(path).lower().endswith((".mid", ".midi")):
            kind = "midi"
        elif str(path).lower().endswith((".mxl", ".xml", ".musicxml")):
            kind = "musicxml"
        elif str(path).lower().endswith(".abc"):
            kind = "abc"
        else:
            raise ValueError(
                "Cannot infer file format from the extension (expect MIDI, "
                "MusicXML or ABC)."
            )
    if kind.lower() == "midi":
        return read_midi(path, **kwargs)
    if kind.lower() == "musicxml":
        return read_musicxml(path, **kwargs)
    if kind.lower() == "abc":
        return read_abc(path, **kwargs)
    raise ValueError(
        f"Expect `kind` to be 'midi', 'musicxml' or 'abc', but got : {kind}."
    )


def from_object(
    obj: Union[Stream, MidiFile, PrettyMIDI, Multitrack], **kwargs
) -> Union[Music, List[Music], Track, List[Track]]:
    """Return an outside object as a Music object.

    Parameters
    ----------
    obj
        Object to convert. Supported objects are `music21.Stream`,
        :class:`mido.MidiTrack`, :class:`pretty_midi.PrettyMIDI`, and
        :class:`pypianoroll.Multitrack` objects.
    **kwargs
        Keyword arguments to pass to :func:`muspy.from_music21`,
        :func:`muspy.from_mido`, :func:`from_pretty_midi` or
        :func:`from_pypianoroll`.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    if isinstance(obj, Stream):
        return from_music21(obj, **kwargs)
    if isinstance(obj, MidiFile):
        return from_mido(obj, **kwargs)
    if isinstance(obj, PrettyMIDI):
        return from_pretty_midi(obj, **kwargs)
    if isinstance(obj, Multitrack):
        return from_pypianoroll(obj, **kwargs)
    raise TypeError(
        "`obj` must be of type music21.Stream, mido.MidiFile, "
        "pretty_midi.PrettyMIDI or pypianoroll.Multitrack."
    )


def from_representation(array: ndarray, kind: str, **kwargs) -> Music:
    """Update with the given representation.

    Parameters
    ----------
    array : :class:`numpy.ndarray`
        Array in a supported representation.
    kind : str, {'pitch', 'pianoroll', 'event', 'note'}
        Data representation type (case-insensitive).
    **kwargs
        Keyword arguments to pass to
        :func:`muspy.from_pitch_representation`,
        :func:`muspy.from_pianoroll_representation`,
        :func:`from_event_representation` or
        :func:`from_note_representation`.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    if kind.lower() in ("pitch", "pitch-based"):
        return from_pitch_representation(array, **kwargs)
    if kind.lower() in ("pianoroll", "piano-roll", "piano roll"):
        return from_pianoroll_representation(array, **kwargs)
    if kind.lower() in ("event", "event-based"):
        return from_event_representation(array, **kwargs)
    if kind.lower() in ("note", "note-based"):
        return from_note_representation(array, **kwargs)
    raise ValueError(
        "Expect `kind` to be 'pitch', 'pianoroll', 'event' or 'note', but"
        f"got : {kind}."
    )
