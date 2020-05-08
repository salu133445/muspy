"""Score visualization interface."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..music import Music


def show_score(music: "Music", **kwargs):
    """Show score visualization."""
    m = music.to_music21()
    m.plot(**kwargs)
