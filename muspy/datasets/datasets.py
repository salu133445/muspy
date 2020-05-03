"""Some simple dataset."""
from pathlib import Path
from typing import Optional, Union

from ..inputs import load
from ..music import Music
from .base import Dataset


class MusicDataset(Dataset):
    """A dataset containing MusPy JSON/YAML files organized as directory.

    The raw data downloaded will be placed in the folder ``{root}/raw``, and
    the converted data will be placed in the folder ``{root}/converted``.

    Attributes
    ----------
    root : str or Path
        Root directory of the dataset.
    kind : {'json', 'yaml'}, optional
        File format of the data. Defaults to 'json'.

    Parameters
    ----------
    download_and_extract : bool, optional
        Whether to download and extract the dataset. Defaults to
        False.

    """

    def __init__(
        self,
        root: Union[str, Path],
        download_and_extract: bool = False,
        kind: str = "json",
    ):
        super().__init__(root, download_and_extract)
        self.kind = kind

        self.filenames = sorted(self.raw_dir.rglob("*." + self.kind))
        (self.raw_dir / ".muspy.success").touch()

    def __getitem__(self, index) -> Music:
        return load(self.root / self.filenames[index], self.kind)

    def __len__(self) -> int:
        return len(self.filenames)


class FolderDataset(Dataset):
    """A dataset containing files organized as directory.

    Two modes are available for this dataset. When the on-the-fly mode is
    enabled, a data sample is converted to a music object on the fly when
    being indexed. When the on-the-fly mode is disabled, a data sample is
    loaded from the precomputed converted data.

    The raw data downloaded will be placed in the folder ``{root}/raw``, and
    the converted data will be placed in the folder ``{root}/converted``.

    To build a custom dataset, it should inherit this class and overide the
    methods ``__getitem__`` and ``__len__`` as well as the class variables
    ``_info``, ``_source`` and ``_extension``, and also the class method
    ``_converter``. Please refer to :class:`muspy.Dataset` for the
    documentation of ``__getitem__``, ``__len__``, ``_info`` and
    ``_source``. ``_extension`` is the extension to look for when building
    the dataset. All the files with the given extension will be included as
    source files. ``_converter`` is a class method that takes as inputs a
    filename of a source file and return the converted Music object.

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
        download: bool = False,
        extract: bool = False,
        cleanup: bool = False,
        convert: bool = False,
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = False,
        use_converted: Optional[bool] = None,
    ):
        super().__init__(root, download, extract, cleanup)
        self.kind = kind
        self._use_converted = use_converted

        self.raw_filenames = sorted(self.raw_dir.rglob("*." + self._extension))
        (self.raw_dir / ".muspy.success").touch()

        if convert:
            self.convert(kind, n_jobs, ignore_exceptions)

        if self._use_converted is None:
            self._use_converted = self.converted_exists()
        elif self._use_converted:
            self.use_converted()

        if self._use_converted:
            self.use_converted()
        else:
            self.converted_filenames: list = []

    def __getitem__(self, index) -> Music:
        if self._use_converted:
            return load(self.root / self.converted_filenames[index], self.kind)
        return self._converter(  # type: ignore
            str(self.root / self.raw_filenames[index])
        )

    def __len__(self) -> int:
        if self._use_converted:
            return len(self.converted_filenames)
        return len(self.raw_filenames)

    @property
    def converted_dir(self):
        """Return the path to the root directory of the converted dataset."""
        return self.root / "converted"

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
        """Convert all the files into Music object and save them to disk.

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
        self.save(self.converted_dir, kind, n_jobs, ignore_exceptions)
        self.converted_filenames = sorted(
            self.converted_dir.rglob("*." + kind)
        )
        self._use_converted = True
        self.kind = kind
        return self
