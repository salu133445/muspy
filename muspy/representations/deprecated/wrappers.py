"""Wrappers for representation utilities."""
from typing import TYPE_CHECKING

from .event import to_event_representation
from .note import to_note_representation
from .pianoroll import to_pianoroll_representation
from .mono_token import to_mono_token_representation

if TYPE_CHECKING:
    from ..music import Music


def to_representation(music: "Music", target: str, **kwargs):
    """Convert to a target representation.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted. The file format is inferred from
        the extension.
    target : str
        Target representation. Supported values are 'event', 'note',
        'pianoroll' and "piano-roll".

    """
    if target.lower() in ("event", "event-based"):
        return to_event_representation(music, **kwargs)
    if target.lower() in ("note", "note-based"):
        return to_note_representation(music, **kwargs)
    if target.lower() in ("pianoroll", "piano-roll"):
        return to_pianoroll_representation(music, **kwargs)
    if target.lower() in ("mono-token", "monotoken"):
        return to_mono_token_representation(music, **kwargs)
    raise ValueError("Unsupported target representation : {}.".format(target))
