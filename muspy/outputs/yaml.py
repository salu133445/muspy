"""YAML output interface."""
import gzip
from pathlib import Path
from typing import TYPE_CHECKING, TextIO, Union

from ..utils import yaml_dump

if TYPE_CHECKING:
    from ..music import Music


def save_yaml(
    path: Union[str, Path, TextIO],
    music: "Music",
    skip_missing: bool = True,
    allow_unicode: bool = True,
    compressed: bool = None,
    **kwargs
):
    """Save a Music object to a YAML file.

    Parameters
    ----------
    path : str, Path or TextIO
        Path or file to save the YAML data.
    music : :class:`muspy.Music`
        Music object to save.
    skip_missing : bool, default: True
        Whether to skip attributes with value None or those that are
        empty lists.
    allow_unicode : bool, default: False
        Whether to escape non-ASCII characters. Will be passed to
        :py:func:`json.dumps`.
    compressed : bool, optional
        Whether to save as a compressed YAML file (`.yaml.gz`). Has no
        effect when `path` is a file object. Defaults to infer from the
        extension (`.gz`).
    **kwargs
        Keyword arguments to pass to `yaml.dump`.

    Notes
    -----
    When a path is given, use UTF-8 encoding and gzip compression if
    `compressed=True`.

    """
    data = yaml_dump(
        music.to_ordered_dict(skip_missing=skip_missing, deepcopy=False),
        allow_unicode=allow_unicode,
        **kwargs
    )

    if isinstance(path, (str, Path)):
        if compressed is None:
            if str(path).lower().endswith(".gz"):
                compressed = True
            else:
                compressed = False
        if compressed:
            with gzip.open(path, "wt", encoding="utf-8") as f:
                f.write(data)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        return

    path.write(data)
