"""YAML input interface."""
from pathlib import Path
from typing import Union

import yaml

from ..music import Music


def load_yaml(path: Union[str, Path]) -> Music:
    """Load a YAML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the file to load.

    Returns
    -------
    :class:`muspy.Music`
        Loaded Music object.

    """
    with open(str(path), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Music.from_dict(data)
