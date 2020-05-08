"""Visualization interface."""
from typing import TYPE_CHECKING, Any

from .pianoroll import show_pianoroll
from .score import show_score

if TYPE_CHECKING:
    from ..music import Music


def show(music: "Music", kind: str, **kwargs: Any):
    """Show visualization."""
    if kind == "pianoroll":
        return show_pianoroll(music, **kwargs)
    if kind == "score":
        return show_score(music, **kwargs)
    raise ValueError("`kind` must be one of 'pianoroll' and 'score'.")
