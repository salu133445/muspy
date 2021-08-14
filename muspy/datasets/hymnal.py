"""Hymnal Dataset."""
from pathlib import Path
from typing import Union

import requests

from ..inputs import read_midi
from ..music import Music
from .base import DatasetInfo, FolderDataset

_NAME = "Hymnal Dataset"
_DESCRIPTION = """\
The Hymnal Dataset is a collection of hymns in MIDI format available at
hymnal.net."""
_HOMEPAGE = "https://www.hymnal.net/"


class HymnalDataset(FolderDataset):
    """Hymnal Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _extension = "mid"
    _type = "mid"

    def __init__(
        self,
        root: Union[str, Path],
        download: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        use_converted: bool = None,
    ):
        self.root = Path(root).expanduser().resolve()
        if not self.root.exists():
            raise ValueError("`root` must be an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        if download:
            self.download()

        super().__init__(
            root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)

    def download(self) -> "FolderDataset":
        """Download the source datasets.

        Returns
        -------
        Object itself.

        """
        # Maximum consecutive trials allowed to fail
        tolerance = 10

        kinds = ["Classic", "New Tunes", "New Songs", "Children"]
        keys = ["h", "nt", "ns", "c"]

        print("Downloading sources.")
        for kind, key in zip(kinds, keys):
            # Make sure the folder exists
            (self.root / kind).mkdir(exist_ok=True)

            # Reset the index and the consecutive failure counter
            idx = 1
            consecutive_failure_count = 0

            # Loop until the number of consecutive failures exceed
            # the tolerance
            while consecutive_failure_count < tolerance:
                # Send a HEAD request to check if content type is MIDI
                url = (
                    f"https://www.hymnal.net/en/hymn/{key}/{idx}/"
                    f"f={self._type}"
                )
                req = requests.head(url)
                if req.headers["Content-Type"] != "audio/midi":
                    consecutive_failure_count += 1
                    continue

                # Send another HEAD request to check if we have
                # exceeded the total number of pieces -> When we request
                # for an out of bound index, it seems that it will
                # randomly return another piece. Thus, if the first and
                # the second requests have different content sizes, we
                # can break the loop.
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

                if idx % 100 == 0:
                    print(f"Successfully downloaded {idx} files.")

        (self.root / ".muspy.success").touch(exist_ok=True)
        return self


class HymnalTuneDataset(FolderDataset):
    """Hymnal Dataset (tune only)."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _extension = "mid"
    _type = "tune"

    def __init__(
        self,
        root: Union[str, Path],
        download: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        use_converted: bool = None,
    ):

        self.root = Path(root).expanduser().resolve()
        if not self.root.exists():
            raise ValueError("`root` must be an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        if download:
            self.download()

        super().__init__(
            root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )

    def read(self, filename: Union[str, Path]) -> Music:
        """Read a file into a Music object."""
        return read_midi(self.root / filename)

    def download(self) -> "FolderDataset":
        """Download the source datasets.

        Returns
        -------
        Object itself.

        """
        # Maximum consecutive trials allowed to fail
        tolerance = 10

        kinds = ["Classic", "New Tunes", "New Songs", "Children"]
        keys = ["h", "nt", "ns", "c"]

        print("Downloading sources.")
        for kind, key in zip(kinds, keys):
            # Make sure the folder exists
            (self.root / kind).mkdir(exist_ok=True)

            # Reset the index and the consecutive failure counter
            idx = 1
            consecutive_failure_count = 0

            # Loop until the number of consecutive failures exceed
            # the tolerance
            while consecutive_failure_count < tolerance:
                # Send a HEAD request to check if content type is MIDI
                url = (
                    f"https://www.hymnal.net/en/hymn/{key}/{idx}/"
                    f"f={self._type}"
                )
                req = requests.head(url)
                if req.headers["Content-Type"] != "audio/midi":
                    consecutive_failure_count += 1
                    continue

                # Send another HEAD request to check if we have
                # exceeded the total number of pieces -> When we request
                # for an out of bound index, it seems that it will
                # randomly return another piece. Thus, if the first and
                # the second requests have different content sizes, we
                # can break the loop.
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

                if idx % 100 == 0:
                    print(f"Successfully downloaded {idx} files.")

        (self.root / ".muspy.success").touch(exist_ok=True)
        return self
