"""JSON output interface."""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from ..music import Music


def save_json(
    path: Union[str, Path],
    music: "Music",
    ensure_ascii: bool = False,
    indent: Optional[Union[int, str]] = None,
):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    path : str or Path
        Path to save the JSON file.
    music : :class:`muspy.Music`
        Music object to save.
    ensure_ascii : bool
        Whether to escape non-ASCII characters. Defaults to False. See
        :py:func:`json.dumps`.
    indent : int or str
        Indent level. See :py:func:`json.dumps`.

    """
    with open(str(path), "w", encoding="utf-8") as f:
        data = music.to_ordered_dict()
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
