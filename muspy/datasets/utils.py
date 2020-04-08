"""Dataset utilities."""
import gzip
import hashlib
import os
import os.path
import shutil
import tarfile
import urllib
import zipfile
from pathlib import Path
from typing import Optional, Union

import requests
from tqdm import tqdm


class _ProgressBar:
    """A callable progress bar object.

    Note
    ----
    Code is adapted from https://stackoverflow.com/a/53643011.
    """

    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if self.pbar is None:
            self.pbar = tqdm(total=total_size)

        downloaded = block_num * block_size
        self.pbar.update(downloaded)


def compute_md5(path: Union[str, Path], chunk_size: int):
    """Return the MD5 checksum of a file, calculated chunk by chunk.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to be read.
    chunk_size : int
        Chunk size used to calculate the MD5 checksum.

    """
    md5 = hashlib.md5()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def check_md5(path: Union[str, Path], md5: str, chunk_size: int = 1024 * 1024):
    """Check if the MD5 checksum of a file matches the expected one.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the file to be check.
    md5 : str, optional
        Expected MD5 checksum of the file.
    chunk_size : int
        Chunk size used to calculate the MD5 checksum.

    """
    return md5 == compute_md5(path, chunk_size)


def download_url(
    url: str, path: Union[str, Path], md5: Optional[str] = None,
):
    """Download a file from a URL.

    Parameters
    ----------
    url : str
        URL to the file to be downloaded.
    path : str or :class:`pathlib.Path`
        Path to save the downloaded file.
    md5 : str, optional
        Expected MD5 checksum of the downloaded file. If None, do not check.

    """
    urllib.request.urlretrieve(url, str(path), reporthook=_ProgressBar())
    if md5 is not None and not check_md5(path, md5):
        raise RuntimeError("Downloaded file is corrupted.")


def _get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


def _save_response_content(response, destination, chunk_size=32768):
    with open(destination, "wb") as f:
        pbar = tqdm(total=None)
        progress = 0
        for chunk in response.iter_content(chunk_size):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                progress += len(chunk)
                pbar.update(progress - pbar.n)


def download_google_drive_file(
    file_id: str, path: Union[str, Path], md5: Optional[str] = None,
):
    """Download a file from Google Drive.

    Parameters
    ----------
    file_id : str
        ID of the the file to be downloaded.
    path : str or :class:`pathlib.Path`
        Path to save the downloaded file.
    md5 : str, optional
        Expected MD5 checksum of the downloaded file. If None, do not check.

    Note
    ----
    Code is adapted from https://stackoverflow.com/a/39225039.

    """
    session = requests.Session()
    url = "https://docs.google.com/uc?export=download"
    response = session.get(url, params={"id": file_id}, stream=True)

    token = _get_confirm_token(response)
    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(url, params=params, stream=True)

    _save_response_content(response, str(path))

    if md5 is not None and not check_md5(path, md5):
        raise RuntimeError("Downloaded file is corrupted.")


def extract_archive(
    path: Union[str, Path],
    root: Optional[Union[str, Path]] = None,
    cleanup: bool = False,
):
    """Extract an archive, with format inferred from the extension.

    Supported extensions are '.tar', '.tar.gz', '.tgz', '.tar.xz', '.txz',
    '.gz' and '.zip'.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        Path to the archive to be extracted.
    root : str or :class:`pathlib.Path`, optional
        Root directory to save the extracted file. If None, use the dirname
        of `path`.
    cleanup : bool
        Whether to remove the original archive. Defaults to False.

    """
    path = str(path)
    if root is None:
        root = os.path.dirname(str(path))

    if path.lower().endswith(".tar"):
        with tarfile.open(str(path), "r") as f:
            f.extractall(path=root)
    elif path.lower().endswith((".tar.gz", ".tgz")):
        with tarfile.open(str(path), "r:gz") as f:
            f.extractall(path=root)
    elif path.lower().endswith((".tar.xz", ".txz")):
        with tarfile.open(str(path), "r:xz") as f:
            f.extractall(path=root)
    elif path.lower().endswith(".gz"):
        filename = os.path.join(
            root, os.path.splitext(os.path.basename(path))[0]
        )
        with gzip.open(str(path), "rb") as f_in, open(filename, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    elif path.lower().endswith(".zip"):
        with zipfile.ZipFile(str(path), "r") as zip_file:
            zip_file.extractall(root)
    else:
        raise ValueError("Extraction of {} not supported".format(path))

    if cleanup:
        os.remove(path)
