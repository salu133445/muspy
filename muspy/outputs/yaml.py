"""YAML output interface."""
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Union

import yaml

if TYPE_CHECKING:
    from ..music import Music


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


def save_yaml(music: "Music", path: Union[str, Path]):
    """Save a Music object to a YAML file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to save.
    path : str or Path
        Path to save the YAML file.

    """
    with open(str(path), "w") as f:
        f.write(_yaml_dump(music.to_ordered_dict()))
