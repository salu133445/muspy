"""JSB Chorales Dataset."""
from .base import MusicDataset


class JSBChoralesDataset(MusicDataset):
    """Johann Sebastian Bach Chorales Dataset."""

    sources = {
        "jsb": {
            "filename": "JSB Chorales.zip",
            "url": "http://www-etud.iro.umontreal.ca/~boulanni/JSB%20Chorales.zip",
            "md5": None,
        }
    }

    default_subsets = ["jsb"]
