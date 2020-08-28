"""Utility functions for working with external dependencies."""
import urllib
from pathlib import Path


def get_bravura_font_dir() -> Path:
    """Return path to the directory of the Bravura font."""
    return Path(__file__).parent / "bravura"


def get_bravura_font_path() -> Path:
    """Return path to the Bravura font."""
    return get_bravura_font_dir() / "Bravura.otf"


def download_bravura_font():
    """Download the Bravura font."""
    # Make sure the directory exists
    get_bravura_font_dir().mkdir(exist_ok=True)

    # Download the font
    prefix = "https://github.com/steinbergmedia/bravura/raw/master/"
    urllib.request.urlretrieve(
        prefix + "redist/otf/Bravura.otf", get_bravura_font_path()
    )

    # Download the license
    urllib.request.urlretrieve(
        prefix + "LICENSE.txt", get_bravura_font_dir() / "LICENSE.txt"
    )


def get_musescore_soundfont_dir() -> Path:
    """Return path to the directory of the MuseScore General soundfont."""
    return Path(__file__).parent / "musescore-general"


def get_musescore_soundfont_path() -> Path:
    """Return path to the MuseScore General soundfont."""
    return get_musescore_soundfont_dir() / "MuseScore_General.sf3"


def download_musescore_soundfont():
    """Download the MuseScore General soundfont."""
    # Make sure the directory exists
    get_musescore_soundfont_dir().mkdir(exist_ok=True)

    # Download the soundfont
    prefix = "ftp://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/"
    urllib.request.urlretrieve(
        prefix + "MuseScore_General.sf3", get_musescore_soundfont_path()
    )

    # Download the license
    urllib.request.urlretrieve(
        prefix + "MuseScore_General_License.md",
        get_musescore_soundfont_dir() / "MuseScore_General_License.md",
    )
