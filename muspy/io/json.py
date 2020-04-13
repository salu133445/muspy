"""JSON I/O utilities."""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import jsonschema

from .utils import from_dict

if TYPE_CHECKING:
    from ..music import Music


def get_json_schema_path() -> str:
    """Return the path to the JSON schema."""
    return str(Path(__file__).resolve().parent / "music.schema.json")


def _load_json(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None
) -> dict:
    """Load data from a JSON file, and validate it by a schema if given."""
    with open(str(path)) as f:
        data = json.load(f)
    if schema_path is not None:
        with open(str(schema_path)) as f:
            schema = json.load(f)
        jsonschema.validate(data, schema)
    return data


def load_json(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None
) -> "Music":
    """Return a Music object loaded from a JSON file.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to br loaded.
    schema_path : str or :class:`pathlib.Path`, optional
        Path to the schema file. If given, validate the loaded data by the
        schema.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    data = _load_json(path, schema_path)
    return from_dict(data)


def save_json(music: "Music", path: Union[str, Path]):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be saved.
    path : str or :class:`pathlib.Path`
        Path to save the JSON file.

    """
    with open(str(path), "w") as f:
        f.write(json.dumps(music.to_ordered_dict()))
