"""Base Dataset classes."""
import json
import warnings
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import numpy as np
from joblib import Parallel, delayed
from numpy.random import RandomState, permutation
from tqdm import tqdm

from ..inputs import load, read_abc_string
from ..music import Music
from ..outputs import save
from .utils import (
    check_md5,
    check_sha256,
    check_size,
    download_url,
    extract_archive,
)

if TYPE_CHECKING:
    from tensorflow.data import Dataset as TFDataset
    from torch.utils.data import Dataset as TorchDataset


RemoteDatasetT = TypeVar("RemoteDatasetT", bound="RemoteDataset")
FolderDatasetT = TypeVar("FolderDatasetT", bound="FolderDataset")


class DatasetInfo:
    """A container for dataset information."""

    def __init__(
        self,
        name: str = None,
        description: str = None,
        homepage: str = None,
        license: str = None,
    ):
        # pylint: disable=redefined-builtin
        self.name = name
        self.description = description
        self.homepage = homepage
        self.license = license

    def __repr__(self) -> str:
        to_join = []
        for attr in ("name", "description", "homepage", "license"):
            if getattr(self, attr) is not None:
                to_join.append(attr + "=" + repr(getattr(self, attr)))
        return "DatasetInfo(" + ", ".join(to_join) + ")"


class Dataset:
    """Base class for MusPy datasets.

    To build a custom dataset, it should inherit this class and overide
    the methods ``__getitem__`` and ``__len__`` as well as the class
    attribute ``_info``. ``__getitem__`` should return the ``i``-th data
    sample as a :class:`muspy.Music` object. ``__len__`` should return
    the size of the dataset. ``_info`` should be a
    :class:`muspy.DatasetInfo` instance storing the dataset information.

    """

    _info: DatasetInfo = DatasetInfo()
    _citation: str = ""

    def __getitem__(self, index) -> Music:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    @classmethod
    def info(cls):
        """Return the dataset infomation."""
        return cls._info

    @classmethod
    def citation(cls):
        """Print the citation infomation."""
        return cls._citation

    def save(
        self,
        root: Union[str, Path],
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        verbose: bool = True,
        **kwargs,
    ):
        """Save all the music objects to a directory.

        Parameters
        ----------
        root : str or Path
            Root directory to save the data.
        kind : {'json', 'yaml'}, default: 'json'
            File format to save the data.
        n_jobs : int, default: 1
            Maximum number of concurrently running jobs. If equal to 1,
            disable multiprocessing.
        ignore_exceptions : bool, default: True
            Whether to ignore errors and skip failed conversions. This
            can be helpful if some source files are known to be
            corrupted.
        verbose : bool, default: True
            Whether to be verbose.
        **kwargs
            Keyword arguments to pass to :func:`muspy.save`.

        """
        if kind not in ("json", "yaml"):
            raise TypeError("`kind` must be either 'json' or 'yaml'.")

        root = Path(root).expanduser().resolve()
        root.mkdir(exist_ok=True)

        def _saver(idx):
            prefix = "0" * (n_digits - len(str(idx)))
            filename = root / (prefix + str(idx) + "." + kind)
            if ignore_exceptions:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        save(filename, self[idx], kind, **kwargs)
                except Exception:  # pylint: disable=broad-except
                    return False
                return True
            save(filename, self[idx], kind, **kwargs)
            return True

        n_digits = len(str(len(self)))

        if verbose:
            print("Converting and saving the dataset...")
        if n_jobs == 1:
            count = 0
            for idx in tqdm(range(len(self))):  # type: ignore
                if _saver(idx):
                    count += 1
        else:
            # TODO: This is slow as `self` is passed between workers.
            results = Parallel(n_jobs=n_jobs, backend="threading", verbose=5)(
                delayed(_saver)(idx) for idx in range(len(self))
            )
            count = results.count(True)
        if verbose:
            print(f"Successfully saved {count} out of {len(self)} files.")

    def split(
        self,
        filename: Union[str, Path] = None,
        splits: Sequence[float] = None,
        random_state: Any = None,
    ) -> Dict[str, List[int]]:
        """Return the dataset as a PyTorch dataset.

        Parameters
        ----------
        filename : str or Path, optional
            If given and exists, path to the file to read the split
            from. If None or not exists, path to save the split.
        splits : float or list of float, optional
            Ratios for train-test-validation splits. If None, return the
            full dataset as a whole. If float, return train and test
            splits. If list of two floats, return train and test splits.
            If list of three floats, return train, test and validation
            splits.
        random_state : int, array_like or RandomState, optional
            Random state used to create the splits. If int or
            array_like, the value is passed to
            :class:`numpy.random.RandomState`, and the created
            RandomState object is used to create the splits. If
            RandomState, it will be used to create the splits.

        """
        if filename is not None and Path(filename).is_file():
            with open(str(filename), encoding="utf-8") as f:
                return json.load(f)

        if not isinstance(splits, (float, list, tuple)):
            raise TypeError("`splits` must be of type float, list or tuple.")

        if isinstance(splits, float):
            if splits <= 0:
                raise ValueError("`splits` must be positive.")
            if splits >= 1:
                raise ValueError("`splits` must be less than 1.")
            splits = [splits, 1 - splits]

        if isinstance(splits, (list, tuple)):
            if sum(splits) != 1:
                raise ValueError("`splits` must sum to 1.")
            if len(splits) < 2 or len(splits) > 3:
                raise ValueError("`splits` must have length 2 or 3.")

        if random_state is None:
            rand_indices = permutation(len(self))
        else:
            if not isinstance(random_state, RandomState):
                random_state = RandomState(random_state)
            rand_indices = random_state.permutation(len(self))

        boundaries = np.cumsum([0.0] + list(splits))
        names = ("train", "test", "validation")
        indices = {}
        for idx, (start, end) in enumerate(
            zip(boundaries[:-1], boundaries[1:])
        ):
            start_idx = int(start * len(self))
            end_idx = int(end * len(self))
            indices[names[idx]] = rand_indices[start_idx:end_idx]

        if filename is not None:
            indices_ = {key: value.tolist() for key, value in indices.items()}
            with open(str(filename), "w", encoding="utf-8") as f:
                f.write(json.dumps(indices_))

        return indices

    def to_pytorch_dataset(
        self,
        factory: Callable = None,
        representation: str = None,
        split_filename: Union[str, Path] = None,
        splits: Sequence[float] = None,
        random_state: Any = None,
        **kwargs: Any,
    ) -> Union["TorchDataset", Dict[str, "TorchDataset"]]:
        """Return the dataset as a PyTorch dataset.

        Parameters
        ----------
        factory : Callable, optional
            Function to be applied to the Music objects. The input is a
            Music object, and the output is an array or a tensor.
        representation : str, optional
            Target representation. See :func:`muspy.to_representation()`
            for available representation.
        split_filename : str or Path, optional
            If given and exists, path to the file to read the split
            from. If None or not exists, path to save the split.
        splits : float or list of float, optional
            Ratios for train-test-validation splits. If None, return the
            full dataset as a whole. If float, return train and test
            splits. If list of two floats, return train and test splits.
            If list of three floats, return train, test and validation
            splits.
        random_state : int, array_like or RandomState, optional
            Random state used to create the splits. If int or
            array_like, the value is passed to
            :class:`numpy.random.RandomState`, and the created
            RandomState object is used to create the splits. If
            RandomState, it will be used to create the splits.

        Returns
        -------
        :class:torch.utils.data.Dataset` or Dict of \
                :class:torch.utils.data.Dataset`
            Converted PyTorch dataset(s).

        """
        if representation is None and factory is None:
            raise TypeError(
                "One of `representation` and `factory` must be given."
            )
        if representation is not None and factory is not None:
            raise TypeError(
                "Only one of `representation` and `factory` can be given."
            )

        try:
            # pylint: disable=import-outside-toplevel
            from torch.utils.data import Dataset as TorchDataset
        except ImportError as err:
            raise ImportError("Optional package pytorch is required.") from err

        class TorchMusicFactoryDataset(TorchDataset):
            """A PyTorch dataset built from a Music dataset.

            Parameters
            ----------
            dataset : :class:`muspy.Dataset`
                Dataset object to base on.
            factory : Callable
                Function to be applied to the Music objects. The input
                is a Music object, and the output is an array or a
                tensor.

            """

            def __init__(
                self,
                dataset: Dataset,
                factory: Callable,
                subset: str = "Full",
                indices: Sequence[int] = None,
            ):
                super().__init__()
                self.dataset = dataset
                self.factory = factory
                self.subset = subset
                self.indices = indices
                if self.indices is not None:
                    self.indices = sorted(
                        idx for idx in self.indices if idx < len(self.dataset)
                    )

            def __repr__(self) -> str:
                return (
                    f"TorchMusicFactoryDataset(dataset={self.dataset}, "
                    f"factory={self.subset}, subset={self.factory})"
                )

            def __getitem__(self, index):
                if self.indices is None:
                    return self.factory(self.dataset[index])
                return self.factory(self.dataset[self.indices[index]])

            def __len__(self) -> int:
                if self.indices is None:
                    return len(self.dataset)
                return len(self.indices)

        class TorchRepresentationDataset(TorchMusicFactoryDataset):
            """A PyTorch music dataset.

            Parameters
            ----------
            dataset : :class:`muspy.Dataset`
                Dataset object to base on.
            representation : str
                Target representation. See
                :func:`muspy.to_representation()` for available
                representation.

            """

            def __init__(
                self,
                dataset: Dataset,
                representation: str,
                subset: str = "Full",
                indices: Sequence[int] = None,
                **kwargs: Any,
            ):
                self.representation = representation

                def factory(music):
                    return music.to_representation(representation, **kwargs)

                super().__init__(
                    dataset, factory=factory, subset=subset, indices=indices
                )

            def __repr__(self) -> str:
                return (
                    f"TorchRepresentationDataset(dataset={self.dataset}, "
                    f"representation={self.representation}, "
                    f"subset={self.subset})"
                )

        # No split
        if splits is None:
            if representation is not None:
                return TorchRepresentationDataset(
                    self, representation, **kwargs
                )
            return TorchMusicFactoryDataset(self, factory)  # type: ignore

        datasets: Dict[str, "TorchDataset"] = {}
        indices_list = self.split(split_filename, splits, random_state)
        for key, value in indices_list.items():
            if representation is not None:
                datasets[key] = TorchRepresentationDataset(
                    self, representation, key, value, **kwargs
                )
            else:

                datasets[key] = TorchMusicFactoryDataset(
                    self, factory, key, value  # type: ignore
                )

        return datasets

    def to_tensorflow_dataset(
        self,
        factory: Callable = None,
        representation: str = None,
        split_filename: Union[str, Path] = None,
        splits: Sequence[float] = None,
        random_state: Any = None,
        **kwargs: Any,
    ) -> Union["TFDataset", Dict[str, "TFDataset"]]:
        """Return the dataset as a TensorFlow dataset.

        Parameters
        ----------
        factory : Callable, optional
            Function to be applied to the Music objects. The input is a
            Music object, and the output is an array or a tensor.
        representation : str, optional
            Target representation. See :func:`muspy.to_representation()`
            for available representation.
        split_filename : str or Path, optional
            If given and exists, path to the file to read the split
            from. If None or not exists, path to save the split.
        splits : float or list of float, optional
            Ratios for train-test-validation splits. If None, return the
            full dataset as a whole. If float, return train and test
            splits. If list of two floats, return train and test splits.
            If list of three floats, return train, test and validation
            splits.
        random_state : int, array_like or RandomState, optional
            Random state used to create the splits. If int or
            array_like, the value is passed to
            :class:`numpy.random.RandomState`, and the created
            RandomState object is used to create the splits. If
            RandomState, it will be used to create the splits.

        Returns
        -------
        :class:tensorflow.data.Dataset` or Dict of
        :class:tensorflow.data.dataset`
            Converted TensorFlow dataset(s).

        """
        if representation is None and factory is None:
            raise TypeError(
                "One of `representation` and `factory` must be given."
            )
        if representation is not None and factory is not None:
            raise TypeError(
                "Only one of `representation` and `factory` can be given."
            )

        try:
            # pylint: disable=import-outside-toplevel
            import tensorflow as tf
            from tensorflow.data import Dataset as TFDataset
        except ImportError as err:
            raise ImportError(
                "Optional package tensorflow is required."
            ) from err

        if representation is not None:

            def _gen(indices):
                for idx in indices:
                    yield self[idx].to_representation(representation, **kwargs)

        else:

            def _gen(indices):
                for idx in indices:
                    yield factory(self[idx])

        # TODO: `from_generator` is slow.

        # No split
        if splits is None:
            indices = np.arange(len(self))
            return TFDataset.from_generator(_gen, tf.float32, args=[indices])

        datasets: Dict[str, TFDataset] = {}
        indices_list = self.split(split_filename, splits, random_state)
        for key, value in indices_list.items():
            indices = np.array(value)
            datasets[key] = TFDataset.from_generator(
                _gen, tf.float32, args=[indices]
            )

        return datasets


class RemoteDataset(Dataset):
    """Base class for remote MusPy datasets.

    This class extends :class:`muspy.Dataset` to support remote
    datasets. To build a custom remote dataset, please refer to the
    documentation of :class:`muspy.Dataset` for details. In addition,
    set the class attribute ``_sources`` to the URLs to the source files
    (see Notes).

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    download_and_extract : bool, default: False
        Whether to download and extract the dataset.
    overwrite : bool, default: False
        Whether to overwrite existing file(s).
    cleanup : bool, default: False
        Whether to remove the source archive(s).
    verbose : bool, default: True
        Whether to be verbose.

    Raises
    ------
    RuntimeError:
        If ``download_and_extract`` is False but file
        ``{root}/.muspy.success`` does not exist (see below).

    Important
    ---------
    :meth:`muspy.Dataset.exists` depends solely on a special file named
    ``.muspy.success`` in directory ``{root}/_converted/``. This file
    serves as an indicator for the existence and integrity of the
    dataset. It will automatically be created if the dataset is
    successfully downloaded and extracted by
    :meth:`muspy.Dataset.download_and_extract`. If the dataset is
    downloaded manually, make sure to create the ``.muspy.success`` file
    in directory ``{root}/_converted/`` to prevent errors.

    Notes
    -----
    The class attribute ``_sources`` is a dictionary storing the
    following information of each source file.

    - filename (str): Name to save the file.
    - url (str): URL to the file.
    - archive (bool): Whether the file is an archive.
    - md5 (str, optional): Expected MD5 checksum of the file.
    - sha256 (str, optional): Expected SHA256 checksum of the file.

    Here is an example.::

        _sources = {
            "example": {
                "filename": "example.tar.gz",
                "url": "https://www.example.com/example.tar.gz",
                "archive": True,
                "md5": None,
                "sha256": None,
            }
        }

    See Also
    --------
    :class:`muspy.Dataset` : Base class for MusPy datasets.

    """

    _sources: Dict[str, dict] = {}

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        overwrite: bool = False,
        cleanup: bool = False,
        verbose: bool = True,
    ):
        super().__init__()
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(exist_ok=True)

        if download_and_extract:
            self.download_and_extract(
                overwrite=overwrite, cleanup=cleanup, verbose=verbose
            )

        if not self.exists():
            raise RuntimeError(
                "Dataset not found. You can download it by passing "
                "`download_and_extract=True`."
            )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(root={self.root})"

    def __getitem__(self, index) -> Music:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def exists(self) -> bool:
        """Return True if the dataset exists, otherwise False."""
        if not (self.root / ".muspy.success").is_file():
            return False
        return True

    def source_exists(self) -> bool:
        """Return True if all the sources exist, otherwise False."""
        for source in self._sources.values():
            filename = self.root / source["filename"]
            if not filename.is_file():
                return False
            if "size" in source and not check_size(filename, source["size"]):
                return False
            if "md5" in source and not check_md5(filename, source["md5"]):
                return False
            if "sha256" in source and not check_sha256(
                filename, source["sha256"]
            ):
                return False
        return True

    def download(
        self: RemoteDatasetT, overwrite: bool = False, verbose: bool = True
    ) -> RemoteDatasetT:
        """Download the dataset source(s).

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing file(s).
        verbose : bool, default: True
            Whether to be verbose.

        Returns
        -------
        Object itself.

        """
        if self.exists():
            if verbose:
                print(
                    "Skip downloading as the `.muspy.success` file is found."
                )
            return self

        for source in self._sources.values():
            download_url(
                source["url"],
                self.root / source["filename"],
                overwrite=overwrite,
                size=source.get("size"),
                md5=source.get("md5"),
                sha256=source.get("sha256"),
                verbose=verbose,
            )
        return self

    def extract(
        self: RemoteDatasetT, cleanup: bool = False, verbose: bool = True
    ) -> RemoteDatasetT:
        """Extract the downloaded archive(s).

        Parameters
        ----------
        cleanup : bool, default: False
            Whether to remove the source archive after extraction.
        verbose : bool, default: True
            Whether to be verbose.

        Returns
        -------
        Object itself.

        """
        if self.exists():
            if verbose:
                print("Skip extracting as the `.muspy.success` file is found.")
            return self

        for source in self._sources.values():
            filename = self.root / source["filename"]
            if source["archive"]:
                extract_archive(
                    filename, self.root, cleanup=cleanup, verbose=verbose
                )
        (self.root / ".muspy.success").touch(exist_ok=True)
        return self

    def download_and_extract(
        self: RemoteDatasetT,
        overwrite: bool = False,
        cleanup: bool = False,
        verbose: bool = True,
    ) -> RemoteDatasetT:
        """Download source datasets and extract the downloaded archives.

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing file(s).
        cleanup : bool, default: False
            Whether to remove the source archive(s).
        verbose : bool, default: True
            Whether to be verbose.

        Returns
        -------
        Object itself.

        """
        return self.download(overwrite=overwrite, verbose=verbose).extract(
            cleanup=cleanup, verbose=verbose
        )


def _get_filenames(root, extensions: List[str], recursive: bool = True):
    filenames = []
    for ext in extensions:
        if recursive:
            filenames.extend(root.rglob(f"*.{ext}"))
        else:
            filenames.extend(root.glob(f"*.{ext}"))
    return filenames


class MusicDataset(Dataset):
    """Class for datasets of MusPy JSON/YAML files.

    Parameters
    ----------
    root : str or Path
        Root directory of the dataset.
    kind : {'json', 'yaml'}, optional
        File formats to include in the dataset. Defaults to include
        both JSON and YAML files.

    Attributes
    ----------
    root : Path
        Root directory of the dataset.
    filenames : list of Path
        Path to the files, relative to `root`.

    See Also
    --------
    :class:`muspy.Dataset` : Base class for MusPy datasets.

    """

    def __init__(self, root: Union[str, Path], kind: str = None):
        if kind is not None and kind not in ("json", "yaml"):
            raise ValueError(f"Unknown value for `kind` : {kind} .")

        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(exist_ok=True)

        if kind is None:
            extensions = ["json", "json.gz", "yaml", "yaml.gz"]
        elif kind == "json":
            extensions = ["json", "json.gz"]
        else:
            extensions = ["yaml", "yaml.gz"]
        self.filenames = _get_filenames(self.root, extensions)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(root={self.root})"

    def __getitem__(self, index) -> Music:
        return load(self.root / self.filenames[index])

    def __len__(self) -> int:
        return len(self.filenames)


class RemoteMusicDataset(MusicDataset, RemoteDataset):
    """Base class for remote datasets of MusPy JSON/YAML files.

    Parameters
    ----------
    root : str or Path
        Root directory of the dataset.
    download_and_extract : bool, default: False
        Whether to download and extract the dataset.
    overwrite : bool, default: False
        Whether to overwrite existing file(s).
    cleanup : bool, default: False
        Whether to remove the source archive(s).
    kind : {'json', 'yaml'}, optional
        File formats to include in the dataset. Defaults to include
        both JSON and YAML files.
    verbose : bool. default: True
        Whether to be verbose.

    Attributes
    ----------
    root : Path
        Root directory of the dataset.
    filenames : list of Path
        Path to the files, relative to `root`.

    See Also
    --------
    :class:`muspy.MusicDataset` :
        Class for datasets of MusPy JSON/YAML files.
    :class:`muspy.RemoteDataset` : Base class for remote MusPy datasets.

    """

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        overwrite: bool = False,
        cleanup: bool = False,
        kind: str = None,
        verbose: bool = True,
    ):
        RemoteDataset.__init__(
            self,
            root,
            download_and_extract=download_and_extract,
            overwrite=overwrite,
            cleanup=cleanup,
            verbose=verbose,
        )
        MusicDataset.__init__(self, root, kind=kind)


class FolderDataset(Dataset):
    """Class for datasets storing files in a folder.

    This class extends :class:`muspy.Dataset` to support folder
    datasets. To build a custom folder dataset, please refer to the
    documentation of :class:`muspy.Dataset` for details. In addition,
    set class attribute ``_extension`` to the extension to look for
    when building the dataset and set ``read`` to a callable that takes
    as inputs a filename of a source file and return the converted Music
    object.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    convert : bool, default: False
        Whether to convert the dataset to MusPy JSON/YAML files. If
        False, will check if converted data exists. If so, disable
        on-the-fly mode. If not, enable on-the-fly mode and warns.
    kind : {'json', 'yaml'}, default: 'json'
        File format to save the data.
    n_jobs : int, default: 1
        Maximum number of concurrently running jobs. If equal to 1,
        disable multiprocessing.
    ignore_exceptions : bool, default: True
        Whether to ignore errors and skip failed conversions. This can
        be helpful if some source files are known to be corrupted.
    use_converted : bool, optional
        Force to disable on-the-fly mode and use converted data.
        Defaults to True if converted data exist, otherwise False.

    Important
    ---------
    :meth:`muspy.FolderDataset.converted_exists` depends solely on a
    special file named ``.muspy.success`` in the folder
    ``{root}/_converted/``, which serves as an indicator for the
    existence and integrity of the converted dataset. If the converted
    dataset is built by :meth:`muspy.FolderDataset.convert`, the
    ``.muspy.success`` file will be created as well. If the converted
    dataset is created manually, make sure to create the
    ``.muspy.success`` file in the folder ``{root}/_converted/`` to
    prevent errors.

    Notes
    -----
    Two modes are available for this dataset. When the on-the-fly mode
    is enabled, a data sample is converted to a music object on the fly
    when being indexed. When the on-the-fly mode is disabled, a data
    sample is loaded from the precomputed converted data.

    See Also
    --------
    :class:`muspy.Dataset` : Base class for MusPy datasets.

    """

    _extension: str = ""

    def __init__(
        self,
        root: Union[str, Path],
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        use_converted: bool = None,
    ):
        self.root = Path(root).expanduser().resolve()
        self.kind = kind

        # A pointer to the callable used to produce the Music object
        self._factory: Callable = lambda: None

        # A pointer to the list of filenames used when indexing
        self._filenames: list = []

        self.raw_filenames: list = []
        self.converted_filenames: list = []

        if convert:
            self.convert(kind, n_jobs, ignore_exceptions)

        if use_converted is None:
            use_converted = self.converted_exists()

        if use_converted:
            self.use_converted()
        else:
            self.on_the_fly()

        if not self._filenames:
            raise ValueError("Nothing found in the directory.")

        (self.root / ".muspy.success").touch()

    @property
    def converted_dir(self):
        """Path to the root directory of the converted dataset."""
        return self.root / "_converted"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(root={self.root})"

    def __getitem__(self, index) -> Music:
        return self._factory(self._filenames[index])

    def __len__(self) -> int:
        return len(self._filenames)

    def read(self, filename: Any) -> Music:
        """Read a file into a Music object."""
        raise NotImplementedError

    def load(self, filename: Union[str, Path]) -> Music:
        """Load a file into a Music object."""
        return load(self.root / filename)

    def exists(self) -> bool:
        """Return True if the dataset exists, otherwise False."""
        if not (self.root / ".muspy.success").is_file():
            return False
        return True

    def converted_exists(self) -> bool:
        """Return True if the saved dataset exists, otherwise False."""
        if not (self.converted_dir / ".muspy.success").is_file():
            return False
        return True

    def get_converted_filenames(self):
        """Return a list of converted filenames."""
        return sorted(self.converted_dir.rglob("*." + self.kind))

    def use_converted(self: FolderDatasetT) -> FolderDatasetT:
        """Disable on-the-fly mode and use converted data.

        Returns
        -------
        Object itself.

        """
        if not self.converted_exists():
            raise RuntimeError(
                "Converted data not found. Run `convert()` to convert "
                "the dataset."
            )
        if not self.converted_filenames:
            self.converted_filenames = self.get_converted_filenames()
        self._filenames = self.converted_filenames
        self._use_converted = True
        self._factory = self.load
        return self

    def get_raw_filenames(self):
        """Return a list of raw filenames."""
        return sorted(
            (
                filename
                for filename in self.root.rglob("*." + self._extension)
                if not str(filename.relative_to(self.root)).startswith(
                    "_converted/"
                )
            )
        )

    def on_the_fly(self: FolderDatasetT) -> FolderDatasetT:
        """Enable on-the-fly mode and convert the data on the fly.

        Returns
        -------
        Object itself.

        """
        if not self.raw_filenames:
            self.raw_filenames = self.get_raw_filenames()
        self._filenames = self.raw_filenames
        self._use_converted = False
        self._factory = self.read
        return self

    def convert(
        self: FolderDatasetT,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        verbose: bool = True,
        **kwargs,
    ) -> FolderDatasetT:
        """Convert and save the Music objects.

        The converted files will be named by its index and saved to
        ``root/_converted``. The original filenames can be found in the
        ``filenames`` attribute. For example, the file at
        ``filenames[i]`` will be converted and saved to ``{i}.json``.

        Parameters
        ----------
        kind : {'json', 'yaml'}, default: 'json'
            File format to save the data.
        n_jobs : int, default: 1
            Maximum number of concurrently running jobs. If equal to 1,
            disable multiprocessing.
        ignore_exceptions : bool, default: True
            Whether to ignore errors and skip failed conversions. This
            can be helpful if some source files are known to be
            corrupted.
        verbose : bool, default: True
            Whether to be verbose.
        **kwargs
            Keyword arguments to pass to :func:`muspy.save`.

        Returns
        -------
        Object itself.

        """
        if self.converted_exists():
            if verbose:
                print("Skip conversion as the `.muspy.success` file is found.")
            return self
        self.on_the_fly()
        self.converted_dir.mkdir(exist_ok=True)
        self.save(
            self.converted_dir,
            kind=kind,
            n_jobs=n_jobs,
            ignore_exceptions=ignore_exceptions,
            verbose=verbose,
            **kwargs,
        )
        (self.converted_dir / ".muspy.success").touch(exist_ok=True)
        self.use_converted()
        self.kind = kind
        return self


class RemoteFolderDataset(FolderDataset, RemoteDataset):
    """Base class for remote datasets storing files in a folder.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    download_and_extract : bool, default: False
        Whether to download and extract the dataset.
    cleanup : bool, default: False
        Whether to remove the source archive(s).
    convert : bool, default: False
        Whether to convert the dataset to MusPy JSON/YAML files. If
        False, will check if converted data exists. If so, disable
        on-the-fly mode. If not, enable on-the-fly mode and warns.
    kind : {'json', 'yaml'}, default: 'json'
        File format to save the data.
    n_jobs : int, default: 1
        Maximum number of concurrently running jobs. If equal to 1,
        disable multiprocessing.
    ignore_exceptions : bool, default: True
        Whether to ignore errors and skip failed conversions. This can
        be helpful if some source files are known to be corrupted.
    use_converted : bool, optional
        Force to disable on-the-fly mode and use converted data.
        Defaults to True if converted data exist, otherwise False.

    See Also
    --------
    :class:`muspy.FolderDataset` :
        Class for datasets storing files in a folder.
    :class:`muspy.RemoteDataset` : Base class for remote MusPy datasets.

    """

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        overwrite: bool = False,
        cleanup: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        use_converted: bool = None,
        verbose: bool = True,
    ):
        RemoteDataset.__init__(
            self,
            root,
            download_and_extract=download_and_extract,
            overwrite=overwrite,
            cleanup=cleanup,
            verbose=verbose,
        )
        FolderDataset.__init__(
            self,
            root,
            convert=convert,
            kind=kind,
            n_jobs=n_jobs,
            ignore_exceptions=ignore_exceptions,
            use_converted=use_converted,
        )

    def read(self, filename: str) -> Music:
        """Read a file into a Music object."""
        raise NotImplementedError


class ABCFolderDataset(FolderDataset):
    """Class for datasets storing ABC files in a folder.

    See Also
    --------
    :class:`muspy.FolderDataset` :
        Class for datasets storing files in a folder.

    """

    _extension = "abc"

    def read(self, filename: Tuple[str, Tuple[int, int]]) -> Music:
        """Read a file into a Music object."""
        filename_, (start, end) = filename
        data = []
        with open(filename_, encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if start <= idx < end and not line.startswith("%"):
                    data.append(line)
        return read_abc_string("".join(data))  # type: ignore

    def on_the_fly(self: FolderDatasetT) -> FolderDatasetT:
        """Enable on-the-fly mode and convert the data on the fly.

        Returns
        -------
        Object itself.

        """
        if not self.raw_filenames:
            filenames = sorted(
                (
                    filename
                    for filename in self.root.rglob("*." + self._extension)
                    if not str(filename.relative_to(self.root)).startswith(
                        "_converted/"
                    )
                )
            )
            self.raw_filenames = []
            for filename in filenames:
                idx = 0
                start = 0
                with open(filename, errors="ignore", encoding="utf-8") as f:

                    # Detect parts in a file
                    for idx, line in enumerate(f):
                        if line.startswith("X:"):
                            if start:
                                self.raw_filenames.append(
                                    (filename, (start, idx))
                                )
                            start = idx

                    # Append the last part
                    if start:
                        self.raw_filenames.append((filename, (start, idx)))

        self._filenames = self.raw_filenames
        self._use_converted = False
        self._factory = self.read
        return self


class RemoteABCFolderDataset(ABCFolderDataset, RemoteDataset):
    """Base class for remote datasets storing ABC files in a folder.

    See Also
    --------
    :class:`muspy.ABCFolderDataset` :
        Class for datasets storing ABC files in a folder.
    :class:`muspy.RemoteDataset` : Base class for remote MusPy datasets.

    """

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        overwrite: bool = False,
        cleanup: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
        use_converted: bool = None,
        verbose: bool = True,
    ):
        RemoteDataset.__init__(
            self,
            root,
            download_and_extract=download_and_extract,
            overwrite=overwrite,
            cleanup=cleanup,
            verbose=verbose,
        )
        ABCFolderDataset.__init__(
            self,
            root,
            convert=convert,
            kind=kind,
            n_jobs=n_jobs,
            ignore_exceptions=ignore_exceptions,
            use_converted=use_converted,
        )
