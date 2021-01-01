"""YAML input interface."""
from pathlib import Path
from typing import TextIO, Union

import yaml

from ..music import Music


def load_yaml(path: Union[str, Path, TextIO]) -> Music:
    """Load a YAML file into a Music object.

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
            return Music.from_dict(yaml.safe_load(f))

    return Music.from_dict(yaml.safe_load(path))
