"""Datasets built from music21 corpus."""
from pathlib import Path
from typing import Optional, Union

from music21 import corpus

from ..inputs import read
from ..music import Music
from .base import Dataset, DatasetInfo, MusicDataset

_NAME = "Music21 Corpus Dataset"
_DESCRIPTION = """Dataset automatically created from a music21 corpus."""
_HOMEPAGE = "https://web.mit.edu/music21/doc/about/referenceCorpus.html"
_CITATION = """\
@inproceedings{cuthbert2010music21,
  author={Michael Scott Cuthbert and Christopher Ariza},
  title={Music21: A Toolkit for Computer-Aided Musicology and Symbolic Music Data},
  booktitle={Proceedings of the 11th International Society for Music Information Retrieval Conference (ISMIR)},
  year=2010
}"""


class Music21Dataset(Dataset):
    """A class of datasets containing files in music21 corpus.

    Parameters
    ----------
    composer : str
        Name of a composer or a collection. Please refer to the music21
        corpus reference page for a full list [1].
    extensions : list of str
        File extensions of desired files.

    References
    ----------
    [1] https://web.mit.edu/music21/doc/about/referenceCorpus.html

    """

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE)
    _citation = _CITATION
    _extensions = (
        ".mid",
        ".midi",
        ".mxl",
        ".xml",
        ".mxml",
        ".musicxml",
        # ".abc",
    )

    def __init__(self, composer: Optional[str] = None):
        if composer is None:
            self.composer = "ALL"
            self.filenames = [
                path
                for path in corpus.corpora.CoreCorpus().getPaths()
                if str(path).endswith(self._extensions)
            ]
        else:
            self.composer = composer
            self.filenames = corpus.getComposer(composer, self._extensions)

    def __repr__(self) -> str:
        return "{}(composer={})".format(type(self).__name__, self.composer)

    def __getitem__(self, index) -> Music:
        if str(self.filenames[index]).lower().endswith(".abc"):
            return read(self.filenames[index], number=0)  # type: ignore
        return read(self.filenames[index])  # type: ignore

    def __len__(self) -> int:
        return len(self.filenames)

    def convert(
        self,
        root: Union[str, Path],
        kind: str = "json",
        n_jobs: int = 1,
        ignore_exceptions: bool = True,
    ) -> "MusicDataset":
        """Convert and save the Music objects.

        Parameters
        ----------
        root : str or Path
            Root directory to save the data.
        kind : {'json', 'yaml'}, optional
            File format to save the data. Defaults to 'json'.
        n_jobs : int, optional
            Maximum number of concurrently running jobs. If equal to 1,
            disable multiprocessing. Defaults to 1.
        ignore_exceptions : bool, optional
            Whether to ignore errors and skip failed conversions. This
            can be helpful if some source files are known to be
            corrupted. Defaults to True.

        """
        self.save(root, kind, n_jobs, ignore_exceptions)
        return MusicDataset(root, kind)
