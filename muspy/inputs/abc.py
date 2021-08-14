"""ABC input interface."""
from pathlib import Path
from typing import List, Union

import music21.converter
from music21.stream import Opus

from ..music import DEFAULT_RESOLUTION, Music
from .music21 import from_music21_opus, from_music21_score


def read_abc_string(
    data_str: str, number: int = None, resolution=DEFAULT_RESOLUTION,
) -> Union[Music, List[Music]]:
    """Read ABC data into Music object(s) using music21 backend.

    Parameters
    ----------
    data_str : str
        ABC data to parse.
    number : int, optional
        Reference number of a specific tune to read (i.e., the 'X:'
        field). Defaults to read all tunes.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object(s).

    """
    # Parse the ABC data using music21
    parsed = music21.converter.parse(data_str, format="abc", number=number)

    # An ABC file can contain multiple songs
    if isinstance(parsed, Opus):
        # Convert the parsed music21 Opus object to MusPy Music objects
        music_list = from_music21_opus(parsed, resolution)

        # Set metadata
        for music in music_list:
            music.metadata.source_format = "abc"

        return music_list

    # Convert the parsed music21 Score object to a MusPy Music object
    music = from_music21_score(parsed, resolution)

    # Set metadata
    music.metadata.source_format = "abc"

    return music


def read_abc(
    path: Union[str, Path], number: int = None, resolution=DEFAULT_RESOLUTION,
) -> Union[Music, List[Music]]:
    """Return an ABC file into Music object(s) using music21 backend.

    Parameters
    ----------
    path : str or Path
        Path to the ABC file to read.
    number : int, optional
        Reference number of a specific tune to read (i.e., the 'X:'
        field). Defaults to read all tunes.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.Music`
        Converted Music object(s).

    """
    # Parse the ABC file using music21
    parsed = music21.converter.parse(path, format="abc", number=number)

    # An ABC file can contain multiple songs
    if isinstance(parsed, Opus):
        # Convert the parsed music21 Opus object to MusPy Music objects
        music_list = from_music21_opus(parsed, resolution)

        # Set metadata
        for music in music_list:
            music.metadata.source_filename = Path(path).name
            music.metadata.source_format = "abc"

        return music_list

    # Convert the parsed music21 Score object to a MusPy Music object
    music = from_music21_score(parsed, resolution)

    # Set metadata
    music.metadata.source_filename = Path(path).name
    music.metadata.source_format = "abc"

    return music
