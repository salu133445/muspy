"""JSON output interface."""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..music import Music


def save_json(path: Union[str, Path], music: "Music"):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    path : str or Path
        Path to save the JSON file.
    music : :class:`muspy.Music` object
        Music object to save.

    """
    with open(str(path), "w") as f:
        f.write(json.dumps(music.to_ordered_dict()))
