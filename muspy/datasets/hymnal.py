"""Hymnal Dataset."""
from pathlib import Path
from typing import Union, Optional

import requests

from ..inputs import read_midi
from .base import DatasetInfo
from .datasets import FolderDataset

_NAME = "Hymnal Dataset"
_DESCRIPTION = """\
The Hymnal Dataset is a collection of hymns in MIDI format available at
hymnal.net.
"""
_HOMEPAGE = "https://www.hymnal.net/"


class HymnalDataset(FolderDataset):
    """Hymnal Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _extension = "mid"
    _type = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)

    def __init__(
        self,
        root: Union[str, Path],
        download: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):

        self.root = Path(root).expanduser()
        if not self.root.exists():
            raise ValueError("`root` must be an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        if download:
            self.download()

        super().__init__(
            root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )

    def download(self) -> "FolderDataset":
        """Download the source datasets."""
        # Maximum consecutive trials allowed to fail
        tolerance = 10

        kinds = ["Classic", "New Tunes", "New Songs", "Children"]
        keys = ["h", "nt", "ns", "c"]

        for kind, key in zip(kinds, keys):
            # Make sure the folder exists
            (self.root / kind).mkdir(exist_ok=True)

            # Reset the index and the consecutive failure counter
            idx = 1
            consecutive_failure_count = 0

            # Loop until the number of consecutive failures exceed tolerance
            while consecutive_failure_count < tolerance:
                # Send a HEAD request to check if the content type is MIDI
                url = "https://www.hymnal.net/en/hymn/{}/{}/f={}".format(
                    key, idx, self._type
                )
                req = requests.head(url)
                if req.headers["Content-Type"] != "audio/midi":
                    consecutive_failure_count += 1
                    continue

                # Send another HEAD request to check if we have exceeded the
                # total number of pieces -> When we request for an out of
                # bound index, it seems that it will randomly return another
                # piece. Thus, if the first and the second requests have
                # different content sizes, we can break the loop.
                second_req = requests.head(url)
                if (
                    second_req.headers["Content-Length"]
                    != req.headers["Content-Length"]
                ):
                    break

                # Send a GET request to get the MIDI file
                req = requests.get(url)
                filename = str(self.root / kind / (str(idx) + ".mid"))
                with open(filename, "wb") as f:
                    f.write(req.content)

                # Reset the consecutive failure counter
                if consecutive_failure_count:
                    consecutive_failure_count = 0

                idx += 1

        (self.root / ".muspy.success").touch(exist_ok=True)
        return self


class HymnalTuneDataset(FolderDataset):
    """Hymnal Dataset (tune only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _extension = "mid"
    _type = "tune"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)

    def __init__(
        self,
        root: Union[str, Path],
        download: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):

        self.root = Path(root).expanduser()
        if not self.root.exists():
            raise ValueError("`root` must be an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        if download:
            self.download()

        super().__init__(
            root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )

    def download(self) -> "FolderDataset":
        """Download the source datasets."""
        # Maximum consecutive trials allowed to fail
        tolerance = 10

        kinds = ["Classic", "New Tunes", "New Songs", "Children"]
        keys = ["h", "nt", "ns", "c"]

        for kind, key in zip(kinds, keys):
            # Make sure the folder exists
            (self.root / kind).mkdir(exist_ok=True)

            # Reset the index and the consecutive failure counter
            idx = 1
            consecutive_failure_count = 0

            # Loop until the number of consecutive failures exceed tolerance
            while consecutive_failure_count < tolerance:
                # Send a HEAD request to check if the content type is MIDI
                url = "https://www.hymnal.net/en/hymn/{}/{}/f={}".format(
                    key, idx, self._type
                )
                req = requests.head(url)
                if req.headers["Content-Type"] != "audio/midi":
                    consecutive_failure_count += 1
                    continue

                # Send another HEAD request to check if we have exceeded the
                # total number of pieces -> When we request for an out of
                # bound index, it seems that it will randomly return another
                # piece. Thus, if the first and the second requests have
                # different content sizes, we can break the loop.
                second_req = requests.head(url)
                if (
                    second_req.headers["Content-Length"]
                    != req.headers["Content-Length"]
                ):
                    break

                # Send a GET request to get the MIDI file
                req = requests.get(url)
                filename = str(self.root / kind / (str(idx) + ".mid"))
                with open(filename, "wb") as f:
                    f.write(req.content)

                # Reset the consecutive failure counter
                if consecutive_failure_count:
                    consecutive_failure_count = 0

                idx += 1

        (self.root / ".muspy.success").touch(exist_ok=True)
        return self
