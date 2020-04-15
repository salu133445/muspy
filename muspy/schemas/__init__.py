"""
Schemas for Music objects
=========================

This module provide functions for working with the JSON and YAML schemas.

"""
from .utils import get_json_schema_path, get_yaml_schema_path
from .version import DEFAULT_SCHEMA_VERSION

__all__ = [
    "DEFAULT_SCHEMA_VERSION",
    "get_json_schema_path",
    "get_yaml_schema_path",
]
