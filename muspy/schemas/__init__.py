"""JSON, YAML and MusicXML schemas.

This module provide functions for working with MusPy's JSON and YAML
schemas and the MusicXML schema.

Functions
---------

- get_json_schema_path
- get_musicxml_schema_path
- get_yaml_schema_path

Variables
---------
- DEFAULT_SCHEMA_VERSION

"""
from .utils import (
    get_json_schema_path,
    get_musicxml_schema_path,
    get_yaml_schema_path,
    validate_json,
    validate_musicxml,
    validate_yaml,
)
from .version import DEFAULT_SCHEMA_VERSION

__all__ = [
    "DEFAULT_SCHEMA_VERSION",
    "get_json_schema_path",
    "get_musicxml_schema_path",
    "get_yaml_schema_path",
    "validate_json",
    "validate_musicxml",
    "validate_yaml",
]
