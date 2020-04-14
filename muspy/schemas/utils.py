"""Schema path utilities."""
from pathlib import Path


def get_json_schema_path() -> str:
    """Return the path to the JSON schema."""
    return str(Path(__file__).resolve().parent / "music.schema.json")


def get_yaml_schema_path() -> str:
    """Return the path to the YAML schema."""
    return str(Path(__file__).resolve().parent / "music.schema.yaml")
