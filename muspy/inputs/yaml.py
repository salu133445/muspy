"""YAML input interface."""
from pathlib import Path
from typing import Optional, Union

import yamale
import yaml

from ..music import Music


def load_yaml(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None
) -> Music:
    """Return a Music object loaded from a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the file to load.
    schema_path : str or Path, optional
        Path to the schema file. If given, validate the loaded data by the
        schema.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded Music object.

    """
    if schema_path is not None:
        data = yamale.make_data(str(path))
        schema = yamale.make_schema(str(schema_path))
        yamale.validate(schema, data)
    with open(str(path)) as f:
        data = yaml.safe_load(f)
    return Music.from_dict(data)
