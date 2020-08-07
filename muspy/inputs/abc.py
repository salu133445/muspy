"""ABC input interface."""
from pathlib import Path
from typing import List, Optional, Union

import music21.converter
from music21.stream import Opus

from ..music import DEFAULT_RESOLUTION, Music
from .music21 import from_music21, from_music21_opus


def read_abc_string(
    data_str: str, number: Optional[int] = None, resolution=DEFAULT_RESOLUTION,
):
    """Read ABC data into Music object(s) using music21 as backend.

    Parameters
    ----------
    data_str : str
        ABC data to parse.
    number : int
        Reference number of a specific tune to read (i.e., the 'X:' field).
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object(s).

    """
    # Parse the ABC data using music21
    parsed = music21.converter.parse(data_str, format="abc", number=number)

    # Convert music21 object(s) to MusPy Music object(s)
    if isinstance(parsed, Opus):
        music_list = from_music21_opus(parsed, resolution)
    else:
        music_list = [from_music21(parsed, resolution)]

    return music_list


def read_abc(
    path: Union[str, Path],
    number: Optional[int] = None,
    resolution=DEFAULT_RESOLUTION,
) -> List[Music]:
    """Return an ABC file into Music object(s) using music21 as backend.

    Parameters
    ----------
    path : str or Path
        Path to the ABC file to read.
    number : int
        Reference number of a specific tune to read (i.e., the 'X:' field).
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Music` objects
        Converted MusPy Music object(s).

    """
    # Parse the ABC file using music21
    parsed = music21.converter.parse(path, format="abc", number=number)

    # Convert music21 object(s) to MusPy Music object(s)
    if isinstance(parsed, Opus):
        music_list = from_music21_opus(parsed, resolution)
    else:
        music_list = [from_music21(parsed, resolution)]

    # Set metadata
    for music in music_list:
        music.metadata.source_filename = Path(path).name
        music.metadata.source_format = "abc"

    return music_list
