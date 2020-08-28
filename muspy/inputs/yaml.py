"""YAML input interface."""
from pathlib import Path
from typing import Union

import yaml

from ..music import Music


def load_yaml(path: Union[str, Path]) -> Music:
    """Return a Music object loaded from a YAML file.

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
        data = yaml.safe_load(f)
    return Music.from_dict(data)
