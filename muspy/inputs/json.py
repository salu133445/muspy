"""JSON input interface."""
import json
from pathlib import Path
from typing import Union

from ..music import Music


def load_json(path: Union[str, Path]) -> Music:
    """Return a Music object loaded from a JSON file.

    Parameters
    ----------
    path : str or Path
        Path to the file to load.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded Music object.

    """
    with open(str(path)) as f:
        data = json.load(f)
    return Music.from_dict(data)
