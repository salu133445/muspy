"""ABC input interface."""
from pathlib import Path
from typing import List, Optional, Union

from music21.converter.subConverters import ConverterABC
from music21.stream import Opus

from ..classes import DEFAULT_RESOLUTION, SourceInfo
from ..music import Music
from .music21 import from_music21, from_music21_opus


def read_abc_string(
    data_str: str,
    ref_number: Optional[int] = None,
    resolution=DEFAULT_RESOLUTION,
):
    """Read ABC data into Music object(s) using music21 as backend.

    Parameters
    ----------
    data_str : str
        ABC data to be parsed.
    ref_number : int
        Reference number of a specific tune to read (i.e., the 'X:' field).
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object(s).

    """
    # Parse the ABC data using music21
    converter = ConverterABC()
    converter.parseData(data_str, ref_number)

    # Convert music21 object(s) to MusPy Music object(s)
    if isinstance(converter.stream, Opus):
        music_list = from_music21_opus(converter.stream, resolution)
    else:
        music_list = [from_music21(converter.stream, resolution)]

    return music_list


def read_abc(
    path: Union[str, Path],
    ref_number: Optional[int] = None,
    resolution=DEFAULT_RESOLUTION,
) -> List[Music]:
    """Return an ABC file into Music object(s) using music21 as backend.

    Parameters
    ----------
    path : str or Path
        Path to the ABC file to be read.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Music` objects
        Converted MusPy Music object(s).

    """
    # Parse the ABC file using music21
    converter = ConverterABC()
    converter.parseFile(path, ref_number)

    # Convert music21 object(s) to MusPy Music object(s)
    if isinstance(converter.stream, Opus):
        music_list = from_music21_opus(converter.stream, resolution)
    else:
        music_list = [from_music21(converter.stream, resolution)]

    # Set meta data
    for music in music_list:
        music.meta.source = SourceInfo(filename=Path(path).name)

    return music_list
