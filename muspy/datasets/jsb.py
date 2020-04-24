"""JSB Chorales Dataset."""
from .base import Dataset


class JSBChoralesDataset(Dataset):
    """Johann Sebastian Bach Chorales Dataset."""

    _sources = {
        "jsb": {
            "filename": "JSB Chorales.zip",
            "url": "http://www-etud.iro.umontreal.ca/~boulanni/JSB%20Chorales.zip",
            "archive": True,
            "md5": None,
        }
    }

    _default_subsets = ["jsb"]
