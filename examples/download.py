"""Download datasets supported by MusPy."""
import argparse
import warnings
from pathlib import Path

import muspy

DATASET_KEYS = [
    "essen",
    "hymnal",
    "hymnal_tune",
    "jsb",
    "lmd",
    "maestro",
    "nes",
    "nmd",
    "wikifonia",
]


def download(key, root):
    """Download the specified dataset."""
    if key == "lmd":
        muspy.LakhMIDIDataset(root, download_and_extract=True)
    elif key == "wikifonia":
        muspy.WikifoniaDataset(root, download_and_extract=True)
    elif key == "nes":
        muspy.NESMusicDatabase(root, download_and_extract=True)
    elif key == "jsb":
        muspy.JSBChoralesDataset(root, download_and_extract=True)
    elif key == "maestro":
        muspy.MAESTRODatasetV2(root, download_and_extract=True)
    elif key == "hymnal":
        muspy.HymnalDataset(root, download=True)
    elif key == "hymnal_tune":
        muspy.HymnalDataset(root, download=True)
    elif key == "nmd":
        muspy.NottinghamDatabase(root, download_and_extract=True)
    elif key == "essen":
        muspy.EssenFolkSongDatabase(root, download_and_extract=True)
    else:
        warnings.warn(
            "Skipped unrecognized dataset identifier : {}.".format(key),
            RuntimeWarning,
        )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Download datasets")

    parser.add_argument("root", help="Root directory to store the dataset(s).")
    parser.add_argument("datasets", nargs="*", help="Dataset identifier(s).")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Download all supported datasets.",
    )

    return parser.parse_args()


def main():
    """Download datasets."""
    args = parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise FileNotFoundError("Root directory must exist.")

    if args.all:
        for dataset in DATASET_KEYS:
            (root / dataset).mkdir(exist_ok=True)
            download(dataset, root / dataset)
    else:
        for dataset in args.datasets:
            (root / dataset).mkdir(exist_ok=True)
            download(dataset.lower(), root / dataset)


if __name__ == "__main__":
    main()
