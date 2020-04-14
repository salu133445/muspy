"""Wrappers for input interface."""
from pathlib import Path
from typing import Union

from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from ..music import Music
from .json import load_json
from .midi import from_pretty_midi, read_midi
from .musicxml import read_musicxml
from .pianoroll import from_pypianoroll
from .yaml import load_yaml


def from_object(obj: Union[PrettyMIDI, Multitrack]) -> Music:
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
        return from_pretty_midi(obj)
    if isinstance(obj, PrettyMIDI):
        return from_pypianoroll(obj)
    raise TypeError(
        "Got unsupported object type (expect PrettyMIDI or Multitrack)."
    )


def read(path: Union[str, Path]) -> Music:
    """Read a MIDI or a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the file to be read. The file format is inferred from the
        extension.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    See Also
    --------
    :func:`muspy.io.load`: load from a JSON or a YAML file

    """
    if str(path).lower().endswith((".mid", ".midi")):
        return read_midi(path)
    if str(path).lower().endswith((".mxl", ".xml", ".mxml", ".musicxml")):
        return read_musicxml(path)
    raise TypeError("Got unsupported file format (expect MIDI or MusicXML).")


def load(path: Union[str, Path]) -> Music:
    """Return a Music object loaded from a JSON or a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the file to be loaded. The file format is inferred from the
        extension.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    See Also
    --------
    :func:`muspy.io.read`: read from other formats such as MIDI and MusicXML

    """
    if str(path).lower().endswith(".json"):
        return load_json(path)
    if str(path).lower().endswith((".yaml", ".yml")):
        return load_yaml(path)
    raise TypeError("Got unsupported file format (expect JSON or YAML).")
