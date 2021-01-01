"""JSON input interface."""
import json
from pathlib import Path
from typing import TextIO, Union

from ..music import Music


def load_json(path: Union[str, Path, TextIO]) -> Music:
    """Load a JSON file into a Music object.

    Parameters
    ----------
    path : str, Path or TextIO
        Path to the file or the file to load.

    Returns
    -------
    :class:`muspy.Music`
        Loaded Music object.

    """
    if isinstance(path, (str, Path)):
        with open(str(path), encoding="utf-8") as f:
            return Music.from_dict(json.load(f))

    return Music.from_dict(json.load(path))
