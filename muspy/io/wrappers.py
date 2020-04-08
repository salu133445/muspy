"""Wrappers for I/O utilities."""
from pathlib import Path
from typing import Union

from ..music import Music
from .midi import read_midi, write_midi
from .musicxml import read_musicxml, write_musicxml
from .json import load_json, save_json
from .yaml import load_yaml, save_yaml


def read(path: Union[str, Path]) -> Music:
    """Read a MIDI or a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to be read. The file format is inferred from the
        extension.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    if str(path).lower().endswith((".mid", ".midi")):
        return read_midi(path)
    if str(path).lower().endswith((".mxml", ".xml")):
        return read_musicxml(path)
    raise TypeError("Got unsupported file format (expect MIDI or MusicXML).")


def write(music: Music, path: Union[str, Path]):
    """Write a MusPy Music object to a MIDI or a MusicXML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted. The file format is inferred from
        the extension.
    path : str or :class:`pathlib.Path`
        Path to write the file. The file format is inferred from the
        extension.

    See Also
    --------
    :meth:`muspy.save`: losslessly save to a JSON and a YAML file

    """
    if str(path).lower().endswith((".mid", ".midi")):
        return write_midi(music, path)
    if str(path).lower().endswith((".mxml", ".xml")):
        return write_musicxml(music, path)
    raise TypeError("Got unsupported file format (expect MIDI or MusicXML).")


def load(path: Union[str, Path]) -> Music:
    """Return a Music object loaded from a JSON or a YAML file.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to be loaded. The file format is inferred from the
        extension.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    if str(path).lower().endswith(".json"):
        return load_json(path)
    if str(path).lower().endswith((".yaml", ".yml")):
        return load_yaml(path)
    raise TypeError("Got unsupported file format (expect JSON or YAML).")


def save(music: Music, path: Union[str, Path]):
    """Save a Music object loselessly to a JSON or a YAML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be saved.
    path : str or :class:`pathlib.Path`
        Path to save the file. The file format is inferred from the
        extension.

    See Also
    --------
    :meth:`muspy.write`: write to other formats such as MIDI and MusicXML

    Notes
    -----
    The conversion can be lossy if any nonserializable object is used (for
    example, in an Annotation object, which can store data of any type).

    """
    if str(path).lower().endswith(".json"):
        return save_json(music, path)
    if str(path).lower().endswith((".yaml", ".yml")):
        return save_yaml(music, path)
    raise TypeError("Got unsupported file format (expect JSON or YAML).")
