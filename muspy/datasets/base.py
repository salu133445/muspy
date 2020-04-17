"""Base MusPy dataset class."""
import warnings
from pathlib import Path
from typing import List, Dict, Optional, Union

from .utils import download_google_drive_file, download_url, extract_archive


class MusicDataset:
    """A base MusPy music dataset.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    download : bool, optional
        Whether to download the dataset after initialization. Defaults to
        False.

    Notes
    -----
    This is the base class for any MusPy music dataset. To add a new
    dataset, please inherit from this class and set the class variables
    `_sources` and `_default_subsets` properly. The dictionary `_sources`
    keeps the information for each source file and the list
    `_default_subsets` contains the subsets to be downloaded by default.

    - filename (str): Name to save the file.
    - url (str): URL to the file.
    - archive (bool): Whether the file is an archive.
    - md5 (str, optional): Expected MD5 checksum of the file.

    Here is an example.::

        _sources = {
            "example": {
                "filename": "example.tar.gz",
                "url": "https://www.example.com/example.tar.gz",
                "archive": True,
                "md5": None,
            }
        }

        _default_subsets = ["example"]

    """

    _sources: Dict = {}
    _default_subsets: List = []

    def __init__(self, root: Union[str, Path], download: bool = False):
        self.root = Path(root).expanduser()
        if download:
            self.download()

    def __repr__(self):
        return "{}(root={})".format(type(self).__name__, self.root)

    def download(
        self,
        subsets: Optional[List[str]] = None,
        extract: bool = True,
        cleanup: bool = False,
    ):
        """Download the source datasets.

        Parameters
        ----------
        subsets : list of str
            Subsets to download. If None, download all subsets.
        extract : bool
            Whether to extract the archive. Defaults to True.
        cleanup : bool
            Whether to remove remove the original archive. Defaults to False.

        """
        if subsets is None:
            subsets = self._default_subsets

        for subset in subsets:
            # Skip unknown subset keys
            if subset not in self._sources:
                warnings.warn(
                    "Skipped unrecognized subset: {}.".format(subset)
                )
                continue

            # Get source information
            source = self._sources[subset]
            filename = self.root / source["filename"]
            md5 = source.get("md5")

            # Download file if it does not exist
            if filename.isfile():
                print(
                    "Skipped existing source : {}.".format(source["filename"])
                )
            else:
                print("Downloading source : {}".format(source["filename"]))
                if source.get("google_drive_id") is not None:
                    download_google_drive_file(
                        source["google_drive_id"], filename, md5
                    )
                else:
                    download_url(source["url"], filename, md5)

            # Extract archive
            if extract and source["archive"]:
                print("Extracting file : {}".format(source["filename"]))
                extract_archive(filename, self.root, cleanup)

    def to_pytorch_dataset(self, representation, transforms=None):
        """Return a PyTorch dataset (`torch.utils.data.dataset`)."""
        # import torch
        pass

    def to_tensorflow_dataset(self, representation, transforms=None):
        """Return a PyTorch dataset (`torch.utils.data.dataset`)."""
        # import tensorflow
        pass

    def pitch2idx(self):
        """
            convert pitch to index
        :return:
        """
        pass

    def idx2pitch(self, inputs, requires_midi=False):
        """
            convert index to pitch

        :return:
        """
        pass

