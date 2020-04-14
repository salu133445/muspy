"""JSON and YAML schemas for MusPy objects."""
from .utils import get_json_schema_path, get_yaml_schema_path
from .version import DEFAULT_SCHEMA_VERSION

__all__ = [
    "DEFAULT_SCHEMA_VERSION",
    "get_json_schema_path",
    "get_yaml_schema_path",
]
