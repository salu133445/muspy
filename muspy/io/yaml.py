"""YAML I/O utilities."""
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Union

import yamale
import yaml

from ..music import Music
from .utils import from_dict


class OrderedDumper(yaml.SafeDumper):
    """A dumper that supports OrderedDict."""

    def increase_indent(self, flow=False, indentless=False):
        return super(OrderedDumper, self).increase_indent(flow, False)


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


OrderedDumper.add_representer(OrderedDict, _dict_representer)


def _yaml_dump(data):
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """
    return yaml.dump(data, Dumper=OrderedDumper)


def get_yaml_schema_path() -> str:
    """Return the path to the YAML schema."""
    return str(Path(__file__).resolve().parent / "music.schema.yaml")


def _load_yaml(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None
) -> dict:
    """Load data from a YAML file, and validate it by a schema if given."""
    if schema_path is not None:
        data = yamale.make_data(str(path))
        schema = yamale.make_schema(str(schema_path))
        yamale.validate(schema, data)
    with open(str(path)) as f:
        data = yaml.safe_load(f)
    return data


def load_yaml(
    path: Union[str, Path], schema_path: Optional[Union[str, Path]] = None
) -> Music:
    """Return a Music object loaded from a YAML file.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to be loaded.
    schema_path : str or :class:`pathlib.Path`, optional
        Path to the schema file. If given, validate the loaded data by the
        schema.

    Returns
    -------
    :class:`muspy.Music` object
        Loaded MusPy Music object.

    """
    data = _load_yaml(path, schema_path)
    return from_dict(data)


def save_yaml(music: Music, path: Union[str, Path]):
    """Save a Music object to a YAML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be saved.
    path : str or :class:`pathlib.Path`
        Path to save the YAML file.

    """
    with open(str(path), "w") as f:
        f.write(_yaml_dump(music.to_ordered_dict()))
