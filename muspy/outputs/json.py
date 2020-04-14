"""JSON output interface."""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..music import Music


def save_json(music: "Music", path: Union[str, Path]):
    """Save a Music object to a JSON file.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be saved.
    path : str or Path
        Path to save the JSON file.

    """
    with open(str(path), "w") as f:
        f.write(json.dumps(music.to_ordered_dict()))
