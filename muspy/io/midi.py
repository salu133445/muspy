"""MIDI I/O utilities."""
from pathlib import Path
from typing import Union

from pretty_midi import PrettyMIDI

from ..music import Music


def from_pretty_midi(pm: PrettyMIDI) -> Music:
    """Return a Music object converted from a PrettyMIDI object.

    Parameters
    ----------
    obj : :class:`pretty_midi.PrettyMIDI` object
        PrettyMIDI object to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    music = Music()
    # TODO: Not implemented yet
    return music


def read_midi(path: Union[str, Path]) -> Music:
    """Read a MIDI file into a Music object.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the MIDI file to be read.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    pm = PrettyMIDI(str(path))
    return from_pretty_midi(pm)


def to_pretty_midi(music: Music) -> PrettyMIDI:
    """Return a PrettyMIDI object converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    pm : :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    """
    pm = PrettyMIDI()
    # TODO: Not implemented yet
    return pm


def write_midi(music: Music, path: Union[str, Path]):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.
    path : str or :class:`pathlib.Path`
        Path to write the MIDI file.

    """
    pm = to_pretty_midi(music)
    pm.write(str(path))
