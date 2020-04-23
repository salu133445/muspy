"""Wrappers for input interface."""
from pathlib import Path
from typing import Any, Optional, Union

from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from ..music import Music
from .event import from_event_representation
from .json import load_json
from .midi import from_pretty_midi, read_midi
from .musicxml import read_musicxml
from .note import from_note_representation
from .pianoroll import from_pianoroll_representation, from_pypianoroll
from .token import from_monotoken_representation, from_polytoken_representation
from .yaml import load_yaml


def load(
    path: Union[str, Path],
    kind: Optional[str] = None,
    schema_path: Optional[Union[str, Path]] = None,
    **kwargs: Any
) -> Music:
    """Return a Music object loaded from a JSON or a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the file to be loaded.
    kind : {'json', 'yaml'}, optional
        Format to save. If None, infer the format from the extension of
        `path`.
    schema_path : str or Path, optional
        Path to the schema file. If given, validate the loaded data by the
        schema.
    **kwargs : dict
        Keyword arguments to be passed to the target function. See
        :func:`muspy.load_json` or :func:`muspy.load_yaml` for available
        arguments.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    See Also
    --------
    :func:`muspy.read`: Read from other formats such as MIDI and MusicXML.

    """
    if kind is None:
        if str(path).lower().endswith(".json"):
            kind = "json"
        if str(path).lower().endswith((".yaml", ".yml")):
            kind = "yaml"
        else:
            raise ValueError(
                "Got unsupported file format (expect JSON or YAML)."
            )
    if kind == "json":
        return load_json(path, schema_path, **kwargs)  # type: ignore
    if kind == "yaml":
        return load_yaml(path, schema_path, **kwargs)  # type: ignore
    raise ValueError("`kind` must be either 'json' or 'yaml'.")


def read(
    path: Union[str, Path], kind: Optional[str] = None, **kwargs: Any
) -> Music:
    """Read a MIDI or a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the file to be read.
    kind : {'midi', 'musicxml'}, optional
        Format to save. If None, infer the format from the extension of
        `path`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    See Also
    --------
    :func:`muspy.load`: Load from a JSON or a YAML file.

    """
    if kind is None:
        if str(path).lower().endswith((".mid", ".midi")):
            kind = "midi"
        if str(path).lower().endswith((".mxl", ".xml", ".mxml", ".musicxml")):
            kind = "musicxml"
        else:
            raise ValueError(
                "Got unsupported file format (expect MIDI or MusicXML)."
            )
    if kind == "midi":
        return read_midi(path, **kwargs)  # type: ignore
    if kind == "musicxml":
        return read_musicxml(path, **kwargs)  # type: ignore
    raise ValueError("`kind` must be either 'midi' or 'musicxml'.")


def from_object(obj: Union[PrettyMIDI, Multitrack], **kwargs: Any) -> Music:
    """Return a Music object converted from a Multitrack or PrettyMIDI object.

    Parameters
    ----------
    obj : :class:`pretty_midi.PrettyMIDI` or :class:`pypianoroll.Multitrack`
    object
        Object to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    if isinstance(obj, PrettyMIDI):
        return from_pretty_midi(obj, **kwargs)  # type: ignore
    if isinstance(obj, Multitrack):
        return from_pypianoroll(obj, **kwargs)  # type: ignore
    raise TypeError(
        "`obj` must be of type pretty_midi.PrettyMIDI or "
        "pypianoroll.Multitrack."
    )


def from_representation(data: ndarray, kind: str, **kwargs: Any) -> Music:
    """Update with the given representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in a supported representation.
    kind : str
        Data representation type. Supported values are 'event', 'note',
        'pianoroll', 'monotoken' and 'polytoken'.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    if kind.lower() in ("event", "event-based"):
        return from_event_representation(data, **kwargs)  # type: ignore
    if kind.lower() in ("note", "note-based"):
        return from_note_representation(data, **kwargs)  # type: ignore
    if kind.lower() in ("pianoroll", "piano-roll"):
        return from_pianoroll_representation(data, **kwargs)  # type: ignore
    if kind.lower() in ("monotoken", "mono-token"):
        return from_monotoken_representation(data, **kwargs)  # type: ignore
    if kind.lower() in ("polytoken", "poly-token"):
        return from_polytoken_representation(data, **kwargs)  # type: ignore
    raise ValueError(
        "`kind` must be one of 'event', 'note', 'pianoroll', 'monotoken' and "
        "'polytoken'."
    )
