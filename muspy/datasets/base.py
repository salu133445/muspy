"""Base MusPy dataset class."""
import os.path
import warnings

from .utils import (
    check_md5,
    download_google_drive_file,
    download_url,
    extract_archive,
)


class MusicDataset:
    """A MusPy music dataset."""

    sources = []
    default_subsets = []

    def __init__(self, root):
        self.root = os.path.expanduser(root)

    def download(self, subsets=None, extract=True, cleanup=False):
        """Download the source datasets.

        Parameters
        ----------
        subsets : list of str
            Subsets to download.
        """
        if subsets is None:
            subsets = self.default_subsets

        for subset in subsets:
            # Skip unknown subset keys
            if subset not in self.sources:
                warnings.warn(
                    "Skipped unrecognized subset: {}.".format(subset)
                )
                continue

            source = self.sources[subset]
            filename = os.path.join(self.root, source["filename"])
            md5 = source.get("md5")

            # Download file if it doest not exist
            if os.path.isfile(filename) and check_md5(filename, md5):
                print("File exists : {}.".format(source["filename"]))
            else:
                print("Downloading file : {}".format(source["filename"]))
                if source.get("google_drive_id") is not None:
                    download_google_drive_file(
                        source["google_drive_id"], self.root, filename, md5
                    )
                else:
                    download_url(source["url"], self.root, filename, md5)

            # Extract archive
            if extract:
                print("Extracting file : {}".format(source["filename"]))
                extract_archive(filename, self.root, cleanup)
