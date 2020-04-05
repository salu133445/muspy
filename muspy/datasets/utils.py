"""Dataset utilities."""
import gzip
import hashlib
import os
import os.path
import shutil
import tarfile
import urllib
import zipfile

import requests
from tqdm import tqdm


class ProgressBar:
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


def compute_md5(filename, chunk_size):
    """Calculate MD5 checksum, chunk by chunk."""
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def check_md5(filename, md5, chunk_size=1024 * 1024):
    """Check if the MD5 checksum of the file matches the give one."""
    return md5 == compute_md5(filename, chunk_size)


def download_url(url, root, filename=None, md5=None):
    """Download a file from a URL to the target root directory.

    Parameters
    ----------
    url : str
        URL to download file from.
    root : str
        Root directory to store the downloaded files.
    filename : str
        Filename to save. If None, infer it from the basename of the URL.
    md5 : str
        MD5 checksum of the download. If None, do not check
    """
    if filename is None:
        filename = os.path.basename(url)
    root = os.path.expanduser(root)
    filename = os.path.join(root, filename)

    # Make sure root directory exists
    os.makedirs(root, exist_ok=True)

    # Download the file
    urllib.request.urlretrieve(url, filename, reporthook=ProgressBar())

    # Check MD5 checksum of the downloaded file
    if not check_md5(filename, md5):
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


def download_google_drive_file(file_id, root, filename=None, md5=None):
    """Download a Google Drive file to the target root directory.

    Parameters
    ----------
    file_id : str
        ID of the target file on .
    root : str
        Directory to place downloaded file in
    filename : str, optional
        Name to save the file under. If None, use the id of the file.
    md5 : str, optional
        MD5 checksum of the download. If None, do not check

    Note
    ----
    Code is adapted from https://stackoverflow.com/a/39225039.
    """
    if filename is None:
        filename = file_id
    root = os.path.expanduser(root)
    filename = os.path.join(root, filename)

    # Make sure root directory exists
    os.makedirs(root, exist_ok=True)

    session = requests.Session()
    url = "https://docs.google.com/uc?export=download"
    response = session.get(url, params={"id": file_id}, stream=True)

    token = _get_confirm_token(response)
    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(url, params=params, stream=True)

    _save_response_content(response, filename)

    # Check MD5 checksum of the downloaded file
    if not check_md5(filename, md5):
        raise RuntimeError("Downloaded file is corrupted.")


def extract_archive(filename, root=None, cleanup=False):
    """Extract an archive with format inferred from the filename."""
    if root is None:
        root = os.path.dirname(filename)

    if filename.endswith(".tar"):
        with tarfile.open(filename, "r") as tar:
            tar.extractall(path=root)
    elif filename.endswith((".tar.gz", ".tgz")):
        with tarfile.open(filename, "r:gz") as tar:
            tar.extractall(path=root)
    elif filename.endswith(".tar.xz"):
        with tarfile.open(filename, "r:xz") as tar:
            tar.extractall(path=root)
    elif filename.endswith(".gz"):
        filepath = os.path.join(
            root, os.path.splitext(os.path.basename(filename))[0]
        )
        with gzip.open(filename, "rb") as f_in, open(filepath, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    elif filename.endswith(".zip"):
        with zipfile.ZipFile(filename, "r") as f:
            f.extractall(root)
    else:
        raise ValueError("Extraction of {} not supported".format(filename))

    if cleanup:
        os.remove(filename)
