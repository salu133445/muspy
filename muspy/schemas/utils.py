"""Utility functions for working with schemas."""
import json
from pathlib import Path
from typing import Union

try:
    import jsonschema

    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

try:
    import xmlschema

    _HAS_XMLSCHEMA = True
except ImportError:
    _HAS_XMLSCHEMA = False

try:
    import yamale

    _HAS_YAMALE = True
except ImportError:
    _HAS_YAMALE = False


def get_json_schema_path() -> str:
    """Return the path to the JSON schema."""
    return str(Path(__file__).resolve().parent / "music.schema.json")


def get_yaml_schema_path() -> str:
    """Return the path to the YAML schema."""
    return str(Path(__file__).resolve().parent / "music.schema.yaml")


def get_musicxml_schema_path() -> str:
    """Return the path to the MusicXML schema."""
    return str(Path(__file__).resolve().parent / "musicxml.xsd")


def validate_json(path: Union[str, Path]):
    """Validate a file against the JSON schema.

    Parameters
    ----------
    path : str or Path
        Path to the file to validate.

    """
    if not _HAS_JSONSCHEMA:
        raise RuntimeError(
            "The jsonschema library is required for JSON schema validation. "
            "You could install it by `pip install muspy[schema]`."
        )
    with open(str(path), encoding="utf-8") as f:
        data = json.load(f)
    with open(str(get_json_schema_path()), encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(data, schema)


def validate_yaml(path: Union[str, Path]):
    """Validate a file against the YAML schema.

    Parameters
    ----------
    path : str or Path
        Path to the file to validate.

    """
    if not _HAS_YAMALE:
        raise RuntimeError(
            "The Yamale library is required for YAML schema validation. "
            "You could install it by `pip install muspy[schema]`."
        )
    data = yamale.make_data(str(path))
    schema = yamale.make_schema(str(get_yaml_schema_path()))
    yamale.validate(schema, data)


def validate_musicxml(path: Union[str, Path]):
    """Validate a file against the MusicXML schema.

    Parameters
    ----------
    path : str or Path
        Path to the file to validate.

    """
    if not _HAS_XMLSCHEMA:
        raise RuntimeError(
            "The xmlschema library is required for MusicXML schema "
            "validation. You could install it by `pip install muspy[schema]`."
        )
    schema = xmlschema.XMLSchema(get_musicxml_schema_path())
    schema.validate(str(path))
