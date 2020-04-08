"""Utilities."""

from .music import Music
from .classes import (
    Annotation,
    KeySignature,
    Lyric,
    Tempo,
    TimeSignature,
    Track,
)


def append(music: Music, obj):
    """Append an object to the correseponding list.

    Parameters
    ----------
    obj : Muspy objects (see below)
        Object to be appended. Supported object types are
        :class:`Muspy.TimeSignature`, :class:`Muspy.KeySignature`,
        :class:`Muspy.Tempo`, :class:`Muspy.Lyric`,
        :class:`Muspy.Annotation` and :class:`Muspy.Track` objects.

    """
    if isinstance(obj, TimeSignature):
        music.time_signatures.append(obj)
    elif isinstance(obj, KeySignature):
        music.key_signatures.append(obj)
    elif isinstance(obj, Tempo):
        music.tempos.append(obj)
    elif isinstance(obj, Lyric):
        music.lyrics.append(obj)
    elif isinstance(obj, Annotation):
        music.annotations.append(obj)
    elif isinstance(obj, Track):
        music.tracks.append(obj)
    else:
        raise TypeError(
            "Expect TimeSignature, KeySignature, Tempo, Note, Lyric, "
            "Annotation or Track object, but got {}.".format(type(obj))
        )


def sort(music: Music):
    """Sort the time-stamped objects with respect to event time.

    This will sort time signatures, key signatures, tempos, lyrics and
    annotations.

    """
    music.time_signatures.sort(key=lambda x: x.start)
    music.key_signatures.sort(key=lambda x: x.time)
    music.tempos.sort(key=lambda x: x.time)
    music.lyrics.sort(key=lambda x: x.time)
    music.annotations.sort(key=lambda x: x.time)
