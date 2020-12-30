"""JSON output interface."""
import json
from pathlib import Path
from typing import TYPE_CHECKING, TextIO, Union

if TYPE_CHECKING:
    from ..music import Music


def save_json(
    path: Union[str, Path, TextIO],
    music: "Music",
    skip_none: bool = True,
    ensure_ascii: bool = False,
    **kwargs
):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    path : str, Path or TextIO
        Path or file to save the JSON data.
    music : :class:`muspy.Music`
        Music object to save.
    skip_none : bool
        Whether to skip attributes with value None or those that are
        empty lists. Defaults to True.
    ensure_ascii : bool
        Whether to escape non-ASCII characters. Will be passed to
        PyYAML's `yaml.dump`. Defaults to False.
    **kwargs
        Keyword arguments to pass to :py:func:`json.dumps`.

    """
    ordered_dict = music.to_ordered_dict(skip_none=skip_none)
    data = json.dumps(ordered_dict, ensure_ascii=ensure_ascii, **kwargs)

    if isinstance(path, (str, Path)):
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(data)
        return

    path.write(data)
