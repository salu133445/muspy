"""Wrappers for output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .json import save_json
from .midi import to_pretty_midi, write_midi
from .musicxml import write_musicxml
from .pianoroll import to_pypianoroll
from .yaml import save_yaml

if TYPE_CHECKING:
    from ..music import Music


def to_object(music: "Music", target: str) -> Union[PrettyMIDI, Multitrack]:
    """Return a PrettyMIDI or a Multitrack object converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    target : str
        Target class. Supported values are 'pretty_midi' and 'pypianoroll'.

    Returns
    -------
    pm : :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    """
    if target.lower() == "pretty_midi":
        return to_pretty_midi(music)
    if target.lower() == "pypianoroll":
        return to_pypianoroll(music)
    raise ValueError(
        "Got unsupported target class (expect 'pretty_midi' or 'pypianoroll')."
    )


def write(music: "Music", path: Union[str, Path]):
    """Write a MusPy Music object to a MIDI or a MusicXML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted. The file format is inferred from
        the extension.
    path : str or Path
        Path to write the file. The file format is inferred from the
        extension.

    See Also
    --------
    :func:`muspy.save`: Losslessly save to a JSON or a YAML file.

    """
    if str(path).lower().endswith((".mid", ".midi")):
        return write_midi(music, path)
    if str(path).lower().endswith((".mxl", ".xml", ".mxml", ".musicxml")):
        return write_musicxml(music, path)
    raise TypeError("Got unsupported file format (expect MIDI or MusicXML).")


def save(music: "Music", path: Union[str, Path]):
    """Save a Music object loselessly to a JSON or a YAML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be saved.
    path : str or Path
        Path to save the file. The file format is inferred from the
        extension.

    See Also
    --------
    :func:`muspy.write`: Write to other formats such as MIDI and MusicXML.

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
