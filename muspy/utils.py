"""Utilities."""
from typing import Union

from .classes import Note, Track
from .music import Music


def validate_list(list_, name: str):
    """Validate a list of objects by calling their method `validate`."""
    if not isinstance(list_, list):
        raise TypeError("{} must be a list.".format(name))
    for item in list_:
        item.validate()


def append(
    obj1: Union[Music, Track], obj2,
):
    """Append an object to the correseponding list.

    If `obj1` is of type :class:`muspy.Music`, `obj2` can be
    :class:`Muspy.TimeSignature`, :class:`Muspy.KeySignature`,
    :class:`Muspy.Tempo`, :class:`Muspy.Lyric`, :class:`Muspy.Annotation`
    or :class:`Muspy.Track`. If `obj1` is of type :class:`muspy.Track`,
    `obj2` can be :class:`Muspy.Note`, :class:`Muspy.Lyric` or
    :class:`Muspy.Annotation`.

    Parameters
    ----------
    obj : Muspy objects (see below)
        Object to be appended.

    """
    obj1.append(obj2)


def sort(obj: Union[Music, Track]):
    """Sort all the time-stamped objects with respect to event time.

    If a :class:`muspy.Music` is given, this will sort time signatures, key
    signatures, tempos, lyrics and annotations, along with notes, lyrics and
    annotations for each track. If a :class:`muspy.Track` is given, this will
    sort notes, lyrics and annotations.

    Parameters
    ----------
    obj : :class:`muspy.Music` or :class:`muspy.Track`object
        Object to be sorted.

    """
    obj.sort()


def clip(
    obj: Union[Music, Track, Note],
    lower: Union[int, float] = 0,
    upper: Union[int, float] = 127,
):
    """Clip the velocity of each note.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or :class:`muspy.Note`
    object
        Object to be clipped.
    lower : int or float, optional
        Lower bound. Defaults to 0.
    upper : int or float, optional
        Upper bound. Defaults to 127.

    """
    obj.clip(lower, upper)


def transpose(obj: Union[Music, Track, Note], semitone: int):
    """Transpose all the notes by a number of semitones.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or :class:`muspy.Note`
    object
        Object to be transposed.
    semitone : int
        The number of semitones to transpose the notes. A positive value
        raises the pitches, while a negative value lowers the pitches.


    """
    obj.transpose(semitone)


def quantize(music: Music, unit: int = 16, is_symbolic_timing: bool = True):
    """Quantize all the time-stamped objects."""
    # if music.down_beats:
    # if not music.time_signature_changes:
    #     raise ValueError("")
    # first_beat_time = min(
    #     music.time_signature_changes, key=lambda x: x["time"]
    # )
