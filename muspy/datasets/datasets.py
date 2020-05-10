"""Some simple dataset."""
from pathlib import Path
from typing import Optional, Union

from ..inputs import load, read_abc_string
from ..music import Music
from .base import Dataset, RemoteDataset


class MusicDataset(Dataset):
    """A local dataset containing MusPy JSON/YAML files in a folder.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.
    kind : {'json', 'yaml'}, optional
        File format of the data. Defaults to 'json'.

    """

    def __init__(self, root: Union[str, Path], kind: str = "json"):
        self.root = Path(root).expanduser()
        if not self.root.exists():
            raise ValueError("`root` must be an existing path.")
        if not self.root.is_dir():
            raise ValueError("`root` must be a directory.")

        self.kind = kind
        self.filenames = sorted(self.root.rglob("*." + self.kind))

    def __repr__(self) -> str:
        return "{}(root={})".format(type(self).__name__, self.root)

    def __getitem__(self, index) -> Music:
        return load(self.root / self.filenames[index], self.kind)

    def __len__(self) -> int:
        return len(self.filenames)


class RemoteMusicDataset(MusicDataset, RemoteDataset):
    """A dataset containing MusPy JSON/YAML files in a folder.

    This class extended :class:`muspy.RemoteDataset` and
    :class:`muspy.FolderDataset`. Please refer to their documentation for
    details.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.
    kind : {'json', 'yaml'}, optional
        File format of the data. Defaults to 'json'.

    Parameters
    ----------
    download_and_extract : bool, optional
        Whether to download and extract the dataset. Defaults to False.
    cleanup : bool, optional
        Whether to remove the original archive(s). Defaults to False.

    """

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        cleanup: bool = False,
        kind: str = "json",
    ):
        RemoteDataset.__init__(self, root, download_and_extract, cleanup)
        MusicDataset.__init__(self, root, kind)


class FolderDataset(Dataset):
    """A class of datasets containing files in a folder.

    Two modes are available for this dataset. When the on-the-fly mode is
    enabled, a data sample is converted to a music object on the fly when
    being indexed. When the on-the-fly mode is disabled, a data sample is
    loaded from the precomputed converted data.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    convert : bool, optional
        Whether to convert the dataset to MusPy JSON/YAML files. If False,
        will check if converted data exists. If so, disable on-the-fly mode.
        If not, enable on-the-fly mode and warns. Defaults to False.
    kind : {'json', 'yaml'}, optional
        File format to save the data. Defaults to 'json'.
    n_jobs : int, optional
        Maximum number of concurrently running jobs in multiprocessing. If
        equal to 1, disable multiprocessing. Defaults to 1.
    ignore_exceptions : bool, optional
        Whether to ignore errors and skip failed conversions. This can be
        helpful if some of the source files is known to be corrupted.
        Defaults to False.
    use_converted : bool, optional
        Force to disable on-the-fly mode and use stored converted data

    Important
    ---------
    :meth:`muspy.FolderDataset.converted_exists` depends solely on a
    special file named ``.muspy.success`` in the folder
    ``{root}/converted/``, which serves as an indicator for the existence
    and integrity of the converted dataset. If the converted dataset is
    built by :meth:`muspy.FolderDataset.convert`, the ``.muspy.success``
    file will be created as well. If the converted dataset is created
    manually, make sure to create the ``.muspy.success`` file in the folder
    ``{root}/converted/`` to prevent errors.

    Notes
    -----
    This class is extended from :class:`muspy.Dataset`. To build a custom
    dataset based on this class, please refer to :class:`muspy.Dataset` for
    the docmentation of the methods ``__getitem__`` and ``__len__``, and the
    class attribute ``_info``.

    In addition, the class attributes ``_extension`` and ``_converter``
    should be properly set. ``_extension`` is the extension to look for when
    building the dataset. All files with the given extension will be
    included as source files. ``_converter`` is a class method that takes as
    inputs a filename of a source file and return the converted Music
    object.

    See Also
    --------
    :class:`muspy.Dataset` : The base class for all MusPy datasets.

    """

    _extension: str = ""

    @classmethod
    def _converter(cls, filename: str) -> Music:
        raise NotImplementedError

    def __init__(
        self,
        root: Union[str, Path],
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):
        self.root = Path(root)
        self.kind = kind
        self._use_converted = use_converted

        self.filenames = sorted(
            (
                filename
                for filename in self.root.rglob("*." + self._extension)
                if not str(filename.relative_to(self.root)).startswith(
                    "_converted/"
                )
            )
        )
        (self.root / ".muspy.success").touch()

        if convert:
            self.convert(kind, n_jobs, ignore_exceptions)

        if self._use_converted is None:
            self._use_converted = self.converted_exists()

        if self._use_converted:
            self.use_converted()
        else:
            self.converted_filenames: list = []

    def __repr__(self) -> str:
        return "{}(root={})".format(type(self).__name__, self.root)

    def __getitem__(self, index) -> Music:
        if self._use_converted:
            return load(self.root / self.converted_filenames[index], self.kind)
        return self._converter(str(self.root / self.filenames[index]))

    def __len__(self) -> int:
        if self._use_converted:
            return len(self.converted_filenames)
        return len(self.filenames)

    def exists(self) -> bool:
        """Return True if the dataset exists, otherwise False."""
        if not (self.root / ".muspy.success").is_file():
            return False
        return True

    @property
    def converted_dir(self):
        """Return the path to the root directory of the converted dataset."""
        return self.root / "_converted"

    def converted_exists(self) -> bool:
        """Return True if the saved dataset exists, otherwise False."""
        if not (self.converted_dir / ".muspy.success").is_file():
            return False
        return True

    def use_converted(self) -> "FolderDataset":
        """Disable on-the-fly mode and use converted data."""
        if not self.converted_exists():
            raise RuntimeError(
                "Converted data not found. Run `convert()` to convert "
                "the dataset."
            )
        self.converted_filenames = sorted(
            self.converted_dir.rglob("*." + self.kind)
        )
        self._use_converted = True
        return self

    def on_the_fly(self) -> "FolderDataset":
        """Enable on-the-fly mode and convert the data on the fly."""
        self._use_converted = False
        return self

    def convert(
        self,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
    ) -> "FolderDataset":
        """Convert and save the Music objects.

        The converted files will be named by its index and saved to
        ``root/_converted``. The original filenames can be found in the
        ``filenames`` attribute. For example, the file at ``filenames[i]``
        will be converted and saved to ``{i}.json``.

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

        """
        self.converted_dir.mkdir(exist_ok=True)
        self.save(self.converted_dir, kind, n_jobs, ignore_exceptions)
        self.converted_filenames = sorted(
            self.converted_dir.rglob("*." + kind)
        )
        self._use_converted = True
        self.kind = kind
        return self


class RemoteFolderDataset(FolderDataset, RemoteDataset):
    """A class of remote datasets containing files in a folder.

    This class extended :class:`muspy.RemoteDataset` and
    :class:`muspy.FolderDataset`. Please refer to their documentation for
    details.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.

    Parameters
    ----------
    download_and_extract : bool, optional
        Whether to download and extract the dataset. Defaults to False.
    cleanup : bool, optional
        Whether to remove the original archive(s). Defaults to False.
    convert : bool, optional
        Whether to convert the dataset to MusPy JSON/YAML files. If False,
        will check if converted data exists. If so, disable on-the-fly mode.
        If not, enable on-the-fly mode and warns. Defaults to False.
    kind : {'json', 'yaml'}, optional
        File format to save the data. Defaults to 'json'.
    n_jobs : int, optional
        Maximum number of concurrently running jobs in multiprocessing. If
        equal to 1, disable multiprocessing. Defaults to 1.
    ignore_exceptions : bool, optional
        Whether to ignore errors and skip failed conversions. This can be
        helpful if some of the source files is known to be corrupted.
        Defaults to False.
    use_converted : bool, optional
        Force to disable on-the-fly mode and use stored converted data

    See Also
    --------
    :class:`muspy.RemoteDataset` : Base class for remote MusPy datasets.
    :class:`muspy.FolderDataset` : A class of datasets containing files in a
    folder.

    """

    @classmethod
    def _converter(cls, filename: str) -> Music:
        raise NotImplementedError

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        cleanup: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):
        RemoteDataset.__init__(self, root, download_and_extract, cleanup)
        FolderDataset.__init__(
            self, root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )


class ABCFolderDataset(FolderDataset):
    """A class of local datasets containing ABC files in a folder."""

    _extension = "abc"

    @classmethod
    def _converter(cls, filename):
        filename, (start, end) = filename
        data = []
        with open(filename) as f:
            for idx, line in enumerate(f):
                if start <= idx < end and not line.startswith("%"):
                    data.append(line)
        return read_abc_string("".join(data))[0]

    def __init__(
        self,
        root: Union[str, Path],
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):
        super().__init__(
            root, convert, kind, n_jobs, ignore_exceptions, use_converted,
        )

        self.fileparts = []

        # Iterate over the files
        for filename in self.filenames:
            idx = 0
            start = 0
            with open(filename, errors="ignore") as f:

                # Detect parts in a file
                for idx, line in enumerate(f):
                    if line.startswith("X:"):
                        if start:
                            self.fileparts.append((filename, (start, idx)))
                        start = idx

                # Append the last part
                if start:
                    self.fileparts.append((filename, (start, idx)))

    def __len__(self) -> int:
        if self._use_converted:
            return len(self.converted_filenames)
        return len(self.fileparts)

    def __getitem__(self, index) -> Music:
        if self._use_converted:
            return load(self.root / self.converted_filenames[index], self.kind)
        filename = str(self.root / self.fileparts[index][0])
        return self._converter((filename, self.fileparts[index][1]))


class RemoteABCFolderDataset(ABCFolderDataset, RemoteDataset):
    """A class of remote datasets containing ABC files in a folder."""

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        cleanup: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):
        RemoteDataset.__init__(self, root, download_and_extract, cleanup)
        ABCFolderDataset.__init__(
            self, root, convert, kind, n_jobs, ignore_exceptions, use_converted
        )
