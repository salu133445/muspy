"""JSON input interface."""
import json
from pathlib import Path
from typing import Optional, Union

import jsonschema

from ..music import Music


def load_json(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None,
) -> Music:
    """Return a Music object loaded from a JSON file.

    Parameters
    ----------
    path : str or Path
        Path to the file to br loaded.
    schema_path : str or Path, optional
        Path to the schema file. If given, validate the loaded data by the
        schema.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    with open(str(path)) as f:
        data = json.load(f)
    if schema_path is not None:
        with open(str(schema_path)) as f:
            schema = json.load(f)
        jsonschema.validate(data, schema)
    return Music(**data)
