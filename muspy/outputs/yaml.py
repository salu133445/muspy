"""YAML output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..music import Music


def save_yaml(path: Union[str, Path], music: "Music"):
    """Save a Music object to a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to save the YAML file.
    music : :class:`muspy.Music` object
        Music object to save.

    """
    with open(str(path), "w") as f:
        f.write(music.pretty_str())
