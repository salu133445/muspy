"""JSON output interface."""
import gzip
import json
from pathlib import Path
from typing import TYPE_CHECKING, TextIO, Union

if TYPE_CHECKING:
    from ..music import Music


def save_json(
    path: Union[str, Path, TextIO],
    music: "Music",
    skip_missing: bool = True,
    ensure_ascii: bool = False,
    compressed: bool = None,
    **kwargs
):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    path : str, Path or TextIO
        Path or file to save the JSON data.
    music : :class:`muspy.Music`
        Music object to save.
    skip_missing : bool, default: True
        Whether to skip attributes with value None or those that are
        empty lists.
    ensure_ascii : bool, default: False
        Whether to escape non-ASCII characters. Will be passed to
        PyYAML's `yaml.dump`.
    compressed : bool, optional
        Whether to save as a compressed JSON file (`.json.gz`). Has no
        effect when `path` is a file object. Defaults to infer from the
        extension (`.gz`).
    **kwargs
        Keyword arguments to pass to :py:func:`json.dumps`.

    Notes
    -----
    When a path is given, use UTF-8 encoding and gzip compression if
    `compressed=True`.

    """
    data = json.dumps(
        music.to_ordered_dict(skip_missing=skip_missing, deepcopy=False),
        ensure_ascii=ensure_ascii,
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
