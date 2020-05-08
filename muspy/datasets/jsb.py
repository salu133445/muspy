"""JSB Chorales Dataset."""
from pathlib import Path
from typing import Optional, Union

from ..inputs import read_midi
from .base import DatasetInfo
from .datasets import RemoteFolderDataset

_NAME = "JSB Chorales Dataset"
_DESCRIPTION = """\
The JSB Chorales Dataset is a collection of 382 four-part chorales by Johann \
Sebastian Bach. This dataset is used in the paper "Modeling Temporal \
Dependencies in High-Dimensional Sequences: Application to Polyphonic Music \
Generation and Transcription" in ICML 2012. It comes with train, test and \
validation split used in the paper "Harmonising Chorales by Probabilistic \
Inference" in NIPS 2005.
"""
_HOMEPAGE = "http://www-etud.iro.umontreal.ca/~boulanni/icml2012"
_CITATION = """\
@inproceedings{boulangerlewandowski2012modeling,
  author={Nicolas Boulanger-Lewandowski and Yoshua Bengio and Pascal \
Vincent},
  title={Modeling Temporal Dependencies in High-Dimensional Sequences: \
Application to Polyphonic Music Generation and Transcription},
  booktitle={Proceedings of the 29th International Conference on Machine \
Learning (ICML)},
  year={2012}
}
"""


class JSBChoralesDataset(RemoteFolderDataset):
    """Johann Sebastian Bach Chorales Dataset."""

    _info = DatasetInfo(_NAME, _DESCRIPTION, _HOMEPAGE, _CITATION)
    _sources = {
        "jsb": {
            "filename": "JSB Chorales.zip",
            "url": (
                "http://www-etud.iro.umontreal.ca/~boulanni/JSB%20Chorales.zip"
            ),
            "archive": True,
            "md5": None,
        }
    }
    _extension = "mid"

    @classmethod
    def _converter(cls, filename):
        return read_midi(filename)

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
        subset: str = "full",
    ):
        super().__init__(
            root,
            download_and_extract,
            cleanup,
            convert,
            kind,
            n_jobs,
            ignore_exceptions,
            use_converted,
        )
        self.full_filenames = self.filenames.copy()
        self.train_filenames = sorted(
            self.get_subset_root("train").rglob("*." + self._extension)
        )
        self.test_filenames = sorted(
            self.get_subset_root("test").rglob("*." + self._extension)
        )
        self.validation_filenames = sorted(
            self.get_subset_root("valid").rglob("*." + self._extension)
        )
        self.use_subset(subset)

    def __repr__(self) -> str:
        return "{}(root={}, subset={})".format(
            type(self).__name__, self.root, self.subset
        )

    def get_subset_root(self, subset):
        """Return the root path to the subset."""
        if subset not in ("full", "train", "test", "valid"):
            raise ValueError(
                "`subset` must be one of 'full', 'train', 'test' and 'valid'."
            )
        return self.root / "JSB Chorales" / subset

    def use_subset(self, subset):
        """Use a specific subset.

        Parameters
        ----------
        subset : {'full', 'train', 'test', 'valid'}
            Subset to use.
        """
        if subset == "full":
            self.filenames = self.full_filenames
        elif subset == "train":
            self.filenames = self.train_filenames
        elif subset == "test":
            self.filenames = self.test_filenames
        elif subset == "valid":
            self.filenames = self.validation_filenames
        else:
            raise ValueError(
                "`subset` must be one of 'full', 'train', 'test' and 'valid'."
            )
        self.subset = subset
        return self
