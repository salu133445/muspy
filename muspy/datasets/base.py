"""Base MusPy dataset class."""
import warnings
from pathlib import Path
from typing import Dict, Optional, Union

from numpy import ndarray
from tqdm import tqdm

from ..music import Music
from .utils import download_google_drive_file, download_url, extract_archive

try:
    from torch.utils.data import Dataset as TorchDataset

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from joblib import Parallel, delayed

    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class DatasetInfo:
    """A container for dataset information."""

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        homepage: Optional[str] = None,
        citation: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.homepage = homepage
        self.citation = citation

    def __repr__(self):
        return (
            "DatasetInfo(name={}, description={}, homepage={}, citation={})"
            "".format(
                self.name, self.description, self.homepage, self.citation
            )
        )


class Dataset:
    """The base class for all MusPy datasets.

    The raw data downloaded will be placed in folder ``{root}/raw``.

    To build a custom dataset, it should inherit this class and overide the
    methods ``__getitem__`` and ``__len__`` as well as the class variables
    ``_info`` and ``_source``. ``__getitem__`` should return the
    ``i``-th data sample as a :class:`muspy.Music` object.
    ``__len__`` should return the size of the dataset.


    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    download : bool, optional
        Whether to download the raw dataset. Defaults to False.
    extract : bool, optional
        Whether to extract the raw dataset. Defaults to False.
    cleanup : bool, optional
        Whether to remove the original archive. Defaults to False.

    Raises
    ------
    RuntimeError:
        If ``download_and_extract`` is False but file
        ``{root}/raw/.muspy.success`` does not exist (see below).

    Important
    ---------
    :meth:`muspy.Dataset.raw_exists` depends solely on a special file named
    ``.muspy.success`` in the folder ``{root}/raw/``, which serves as an
    indicator for the existence and integrity of the raw dataset. If the raw
    dataset is downloaded and extracted by
    :meth:`muspy.Dataset.download_and_extract`, the ``.muspy.success``
    file will be created as well. If the raw dataset is downloaded manually,
    make sure to create the ``.muspy.success`` file in the folder
    ``{root}/raw/`` to prevent errors.

    Notes
    -----
    Set the class variables ``_sources`` properly. The dictionary ``_sources``
    keeps the information for each source file.

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

    """

    _info: DatasetInfo = DatasetInfo()
    _sources: Dict[str, dict] = {}

    def __init__(
        self,
        root: Union[str, Path],
        download: bool = False,
        extract: bool = False,
        cleanup: bool = False,
    ):
        self.root = Path(root).expanduser()
        if not self.root.exists():
            raise ValueError("`root` must an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        if download:
            self.download()
        if extract:
            self.extract(cleanup)

        if not self.raw_exists():
            raise RuntimeError("Raw dataset not found or corrupted.")

    def __getitem__(self, index) -> Music:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __repr__(self) -> str:
        return "{}(root={})".format(type(self).__name__, self.root)

    @classmethod
    def info(cls):
        """Return the dataset infomation."""
        return cls._info

    @classmethod
    def cite(cls):
        """Return the citation infomation."""
        return cls._info.citation

    @property
    def raw_dir(self):
        """Return the path to root directory of the raw dataset."""
        return self.root / "raw"

    def raw_exists(self) -> bool:
        """Return True if the raw dataset exists, otherwise False."""
        if not (self.raw_dir / ".muspy.success").is_file():
            return False
        return True

    def save(
        self,
        root: Union[str, Path],
        kind: Optional[str] = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
    ):
        """Save all the music objects to a directory.

        The converted files will be named by its index and saved to ``root``.

        Parameters
        ----------
        root : str or Path
            Root directory to save the data.
        kind : {'json', 'yaml'}, optional
            File format to save the data. Defaults to 'json'.
        n_jobs : int, optional
            Maximum number of concurrently running jobs in multiprocessing. If
            equal to 1, disable multiprocessing. Defaults to 1.
        ignore_exceptions : bool, optional
            Whether to ignore errors and skip failed conversions. This can be
            helpful if some of the source files is known to be corrupted.
            Defaults to False.

        Notes
        -----
        The original filenames can be found in the ``filenames`` attribute.
        For example, the file at ``filenames[i]`` will be converted and
        saved to ``{i}.json``.

        """
        if kind not in ("json", "yaml"):
            raise TypeError("`kind` must be either 'json' or 'yaml'.")
        if not isinstance(n_jobs, int):
            raise TypeError("`n_jobs` must be an integer.")
        if n_jobs < 0:
            raise ValueError("`n_jobs` must be positive.")

        root = Path(root)
        root.mkdir(exist_ok=True)

        def _saver(idx):
            if ignore_exceptions:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self[idx].save(root / (str(idx) + "." + kind), kind)
                except Exception:  # pylint: disable=broad-except
                    return False
                return True
            self[idx].save(root / (str(idx) + "." + kind), kind)
            return True

        print("Start converting and saving the dataset...")
        if n_jobs == 1:
            count = 0
            for idx in tqdm(range(len(self))):  # type: ignore
                if _saver(idx):
                    count += 1
        else:
            if not HAS_JOBLIB:
                raise ValueError(
                    "Optional package joblib is required for multiprocessing "
                    "(n_jobs > 1)."
                )
            # TODO: This is slow due to passing `self` between workers.
            results = Parallel(n_jobs=n_jobs, backend="threading", verbose=5)(
                delayed(_saver)(idx) for idx in range(len(self))
            )
            count = results.count(True)
        print(
            "{} out of {} files successfully converted.".format(
                count, len(self)
            )
        )
        (root / ".muspy.success").touch(exist_ok=True)

    def download(self) -> "Dataset":
        """Download the source datasets."""
        self.raw_dir.mkdir(exist_ok=True)
        for source in self._sources.values():
            filename = self.raw_dir / source["filename"]
            md5 = source.get("md5")
            if filename.is_file():
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
        return self

    def extract(self, cleanup: bool = False) -> "Dataset":
        """Extract the downloaded archives.

        Parameters
        ----------
        cleanup : bool, optional
            Whether to remove the original archive. Defaults to False.

        """
        for source in self._sources.values():
            filename = self.raw_dir / source["filename"]
            if source["archive"]:
                print("Extracting archive : {}".format(source["filename"]))
                extract_archive(filename, self.raw_dir, cleanup=cleanup)
        (self.raw_dir / ".muspy.success").touch(exist_ok=True)
        return self

    def download_and_extract(self, cleanup: bool = False) -> "Dataset":
        """Extract the downloaded archives.

        This is equivalent to ``Dataset.download().extract(cleanup)``.

        Parameters
        ----------
        cleanup : bool, optional
            Whether to remove the original archive. Defaults to False.

        """
        return self.download().extract(cleanup)

    def to_pytorch_dataset(self, representation: str) -> "TorchMusicDataset":
        """Return a PyTorch dataset (`torch.utils.data.dataset`)."""
        # TODO: Support slicing and other operations
        if not HAS_TORCH:
            raise ImportError("Optional package torch is required.")
        return TorchMusicDataset(self, representation)


if HAS_TORCH:

    class TorchMusicDataset(TorchDataset):
        """A PyTorch music dataset."""

        def __init__(self, dataset: Dataset, representation: str):
            self.dataset = dataset
            self.representation = representation

        def __getitem__(self, index) -> ndarray:
            return self.dataset[index].to_representation(self.representation)

        def __len__(self) -> int:
            return len(self.dataset)
