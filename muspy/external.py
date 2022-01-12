"""External dependencies.

This module provides functions for working with external dependencies.

Functions
---------

- download_bravura_font
- download_musescore_soundfont
- get_bravura_font_dir
- get_bravura_font_path
- get_musescore_soundfont_dir
- get_musescore_soundfont_path

"""
import urllib.request
from pathlib import Path

__all__ = [
    "download_bravura_font",
    "download_musescore_soundfont",
    "get_bravura_font_dir",
    "get_bravura_font_path",
    "get_musescore_soundfont_dir",
    "get_musescore_soundfont_path",
]


def get_bravura_font_dir() -> Path:
    """Return path to the directory of the Bravura font."""
    return Path.home() / ".muspy/bravura"


def get_bravura_font_path() -> Path:
    """Return path to the Bravura font."""
    return get_bravura_font_dir() / "Bravura.otf"


def download_bravura_font(overwrite: bool = False):
    """Download the Bravura font.

    Parameters
    ----------
    overwrite : bool, default: False
        Whether to overwrite an existing file.

    """
    if not overwrite and get_bravura_font_path().is_file():
        print("Skip downloading as the Bravura font is found.")
        return

    # Make sure the directory exists
    get_bravura_font_dir().mkdir(parents=True, exist_ok=True)

    # Download the font
    print("Start downloading Bravura font.")
    prefix = "https://github.com/steinbergmedia/bravura/raw/master/"
    urllib.request.urlretrieve(
        prefix + "redist/otf/Bravura.otf", get_bravura_font_path()
    )
    print(
        "Bravura font has successfully been downloaded to : "
        f"{get_musescore_soundfont_dir()}."
    )

    # Download the license
    urllib.request.urlretrieve(
        prefix + "LICENSE.txt", get_bravura_font_dir() / "LICENSE.txt"
    )


def get_musescore_soundfont_dir() -> Path:
    """Return path to the MuseScore General soundfont directory."""
    return Path.home() / ".muspy/musescore-general"


def get_musescore_soundfont_path() -> Path:
    """Return path to the MuseScore General soundfont."""
    return get_musescore_soundfont_dir() / "MuseScore_General.sf3"


def download_musescore_soundfont(overwrite: bool = False):
    """Download the MuseScore General soundfont.

    Parameters
    ----------
    overwrite : bool, default: False
        Whether to overwrite an existing file.

    """
    if not overwrite and get_musescore_soundfont_path().is_file():
        print("Skip downloading as the MuseScore General soundfont is found.")
        return

    # Make sure the directory exists
    get_musescore_soundfont_dir().mkdir(parents=True, exist_ok=True)

    # Download the soundfont
    print("Start downloading MuseScore General soundfont.")
    prefix = "ftp://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/"
    urllib.request.urlretrieve(
        prefix + "MuseScore_General.sf3", get_musescore_soundfont_path()
    )
    print(
        "MuseScore General soundfont has successfully been downloaded to : "
        f"{get_musescore_soundfont_dir()}."
    )

    # Download the license
    urllib.request.urlretrieve(
        prefix + "MuseScore_General_License.md",
        get_musescore_soundfont_dir() / "MuseScore_General_License.md",
    )
