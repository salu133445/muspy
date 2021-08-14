"""Visualization interface."""
from typing import TYPE_CHECKING, Any

from .pianoroll import show_pianoroll
from .score import show_score

if TYPE_CHECKING:
    from ..music import Music


def show(music: "Music", kind: str, **kwargs: Any):
    """Show visualization.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to convert.
    kind : {'piano-roll', 'score'}
        Target representation.

    """
    if kind.lower() in ("piano-roll", "pianoroll", "piano roll"):
        return show_pianoroll(music, **kwargs)
    if kind.lower() == "score":
        return show_score(music, **kwargs)
    raise ValueError("`kind` must be one of 'piano-roll' and 'score'.")
