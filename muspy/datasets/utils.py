"""Utility functions for dataset classes."""
import gzip
import hashlib
import lzma
import os
import os.path
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Union
from urllib.request import urlretrieve

from tqdm import tqdm


class _ProgressBar:
    """A callable progress bar object.

    Code is adapted from https://stackoverflow.com/a/53643011.

    """

    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if self.pbar is None:
            self.pbar = tqdm(total=total_size)

        downloaded = block_num * block_size
        self.pbar.update(downloaded)


def check_size(path: Union[str, Path], size: int):
    """Check if the size of a file matches the expected one.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    size : str
        Expected size of the file.

    """
    return Path(path).stat().st_size == size


def compute_md5(path: Union[str, Path], chunk_size: int):
    """Return the MD5 hash of a file, calculated chunk by chunk.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    chunk_size : int
        Chunk size used to calculate the MD5 hash.

    """
    md5 = hashlib.md5()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def check_md5(path: Union[str, Path], md5: str, chunk_size: int = 1024 * 1024):
    """Check if the MD5 hash of a file matches the expected one.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    md5 : str
        Expected MD5 hash of the file.
    chunk_size : int, default: 2^20
        Chunk size used to compute the MD5 hash.

    """
    return compute_md5(path, chunk_size) == md5


def compute_sha256(path: Union[str, Path], chunk_size: int):
    """Return the MD5 checksum of a file, calculated chunk by chunk.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    chunk_size : int
        Chunk size used to calculate the MD5 checksum.

    """
    sha256 = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_sha256(
    path: Union[str, Path], sha256: str, chunk_size: int = 1024 * 1024
):
    """Check if the sha256 hash of a file matches the expected one.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    sha256 : str
        Expected sha256 hash of the file.
    chunk_size : int, default: 2^20
        Chunk size used to compute the sha256 hash.

    """
    return compute_sha256(path, chunk_size) == sha256


def download_url(
    url: str,
    path: Union[str, Path],
    overwrite: bool = False,
    size: int = None,
    md5: str = None,
    sha256: str = None,
    verbose: bool = True,
):
    """Download a file from a URL.

    Parameters
    ----------
    url : str
        URL to the file to download.
    path : str or Path
        Path to save the downloaded file.
    overwrite : bool, default: False
        Whether to overwrite existing downloaded file.
    size : int, optional
        Expected size of the downloaded file. Defaults to skip size
        check.
    md5 : str, optional
        Expected MD5 checksum of the downloaded file. Defaults to skip
        MD5 check.
    sha256 : str, optional
        Expected sha256 checksum of the downloaded file. Defaults to
        skip sha256 check.
    verbose : bool, default: True
        Whether to be verbose.

    """
    path = Path(path)
    if not overwrite and path.is_file():
        if size is not None and not check_size(path, size):
            raise RuntimeError(
                "Existing file has a different size from the expected one."
            )
        if md5 is not None and not check_md5(path, md5):
            raise RuntimeError(
                "Existing file has a different md5 hash from the expected one."
            )
        if sha256 is not None and not check_sha256(path, sha256):
            raise RuntimeError(
                "Existing file has a different sha256 hash from the expected "
                "one."
            )
        if verbose:
            print(f"Found existing downloaded file : {path} .")
        return

    # Download the file
    if verbose:
        print(f"Downloading source : {url} ...")
        urlretrieve(url, path, reporthook=_ProgressBar())
        print(f"Successfully downloaded source : {path} .")
    else:
        urlretrieve(url, path)

    # Run checks
    if size is not None and not check_size(path, size):
        raise RuntimeError(
            "Downloaded file has a different size from the expected one."
        )
    if md5 is not None and not check_md5(path, md5):
        raise RuntimeError(
            "Downloaded file has a different md5 hash from the expected one."
        )
    if sha256 is not None and not check_sha256(path, sha256):
        raise RuntimeError(
            "Downloaded file has a different sha256 hash from the expected "
            "one."
        )


def extract_archive(
    path: Union[str, Path],
    root: Union[str, Path] = None,
    kind: str = None,
    cleanup: bool = False,
    verbose: bool = True,
):
    """Extract an archive in ZIP, TAR, TGZ, TXZ, GZ or XZ format.

    Parameters
    ----------
    path : str or Path
        Path to the archive.
    root : str or Path, optional
        Root directory to save the extracted file. Defaults to the
        directory that contains the archive.
    kind : {'zip', 'tar', 'tgz', 'txz', 'gz', 'xz'}, optional
        Fromat of the archive. Defaults to infer from the extension.
    cleanup : bool, default: False
        Whether to remove the source archive after extraction.
    verbose : bool, default: True
        Whether to be verbose.

    """
    path = Path(path)
    root = Path(root) if root is not None else path.parent
    if kind is None:
        std_path = str(path)
        if std_path.endswith(".zip"):
            kind = "zip"
        elif std_path.endswith(".tar"):
            kind = "tar"
        elif std_path.endswith((".tar.gz", ".tgz")):
            kind = "tgz"
        elif std_path.endswith((".tar.xz", ".txz")):
            kind = "txz"
        elif std_path.endswith(".gz"):
            kind = "gz"
        elif std_path.endswith(".xz"):
            kind = "xz"
        else:
            raise ValueError(
                "Cannot infer file format from the extension (expect ZIP, "
                "TAR, TGZ, TXZ, GZ or XZ)."
            )

    # Extract archive
    if kind in ("zip", "tar", "tgz", "txz"):

        if verbose:
            print(f"Extracting archive : {path} ...")

        # zip file
        if kind == "zip":
            with zipfile.ZipFile(path, "r") as zip_file:
                zip_file.extractall(root)

        # tar file
        else:
            if kind == "tar":
                mode = "r"
            elif kind == "tgz":
                mode = "r:gz"
            elif kind == "txz":
                mode = "r:xz"
            with tarfile.open(path, mode) as f:
                f.extractall(root)

        if verbose:
            print(f"Successfully extracted archive : {root} .")

    elif kind in ("gz", "xz"):

        if verbose:
            print(f"Extracting archive : {path} ...")
        filename = root / path.stem

        # gzip file
        if kind == "gz":
            with gzip.open(path, "rb") as f_in, open(filename, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # xz file
        else:
            with lzma.open(path, "rb") as f_in_, open(filename, "wb") as f_out:
                shutil.copyfileobj(f_in_, f_out)

        if verbose:
            print(f"Successfully extracted archive : {filename} .")

    else:
        raise ValueError(
            "Expect `kind` to be one of 'zip', 'tar', 'tgz', 'txz', 'gz', "
            f"'xz' or , but got : {kind}."
        )

    # Cleanup source archive
    if cleanup:
        os.remove(path)
        if verbose:
            print("Removed source archive : {path} .")
