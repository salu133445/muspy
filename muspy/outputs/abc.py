"""ABC output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

from .music21 import to_music21

if TYPE_CHECKING:
    from ..music import Music


def write_abc(path: Union[str, Path], music: "Music"):
    """Write a Music object to a ABC file.

    Parameters
    ----------
    path : str or Path
        Path to write the ABC file.
    music : :class:`muspy.Music` object
        Music object to write.

    """
    score = to_music21(music)
    score.write("abc", str(path))
