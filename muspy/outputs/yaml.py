"""YAML output interface."""
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
    **kwargs
):
    """Save a Music object to a YAML file.

    Parameters
    ----------
    path : str, Path or TextIO
        Path or file to save the YAML data.
    music : :class:`muspy.Music`
        Music object to save.
    skip_missing : bool
        Whether to skip attributes with value None or those that are
        empty lists. Defaults to True.
    allow_unicode : bool
        Whether to escape non-ASCII characters. Will be passed to
        :py:func:`json.dumps`. Defaults to False.
    **kwargs
        Keyword arguments to pass to :py:func:`json.dumps`.

    """
    ordered_dict = music.to_ordered_dict(skip_missing=skip_missing)
    data = yaml_dump(ordered_dict, allow_unicode=allow_unicode, **kwargs)

    if isinstance(path, (str, Path)):
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(data)
        return

    path.write(data)
