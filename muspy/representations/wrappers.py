"""Wrappers for representation utilities."""
from ..music import Music
from .event import to_event_representation
from .note import to_note_representation
from .pianoroll import to_pianoroll_representation


def to_representation(music: Music, target: str):
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
        return to_event_representation(music)
    if target.lower() in ("note", "note-based"):
        return to_note_representation(music)
    if target.lower() in ("pianoroll", "piano-roll"):
        return to_pianoroll_representation(music)
    raise ValueError("Unsupported target representation : {}.".format(target))
