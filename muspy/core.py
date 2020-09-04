"""Functions for MusPy objects.

This module defines functions that can be applied to a MusPy object.

Functions
---------

- adjust_resolution
- adjust_time
- append
- clip
- get_end_time
- get_real_end_time
- remove_duplicate
- sort
- to_ordered_dict
- transpos

"""
from collections import OrderedDict
from typing import Callable, Optional, Union

from .base import Base, ComplexBase
from .classes import Note, Track
from .music import Music

__all__ = [
    "adjust_resolution",
    "adjust_time",
    "append",
    "clip",
    "get_end_time",
    "get_real_end_time",
    "remove_duplicate",
    "sort",
    "to_ordered_dict",
    "transpose",
]


def adjust_resolution(
    music: Music, target: Optional[int] = None, factor: Optional[float] = None
) -> Music:
    """Adjust resolution and update the timing of time-stamped objects.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy music object to adjust.
    target : int, optional
        Target resolution.
    factor : int or float, optional
        Factor used to adjust the resolution based on the formula:
        `new_resolution = old_resolution * factor`. For example, a factor of
        2 double the resolution, and a factor of 0.5 halve the resolution.

    """
    return music.adjust_resolution(target=target, factor=factor)


def adjust_time(obj: Base, func: Callable[[int], int]) -> Base:
    """Adjust the timing of time-stamped objects.

    Parameters
    ----------
    obj : :class:`muspy.Music` or :class:`muspy.Track` object
        Object to adjust.
    func : callable
        The function used to compute the new timing from the old timing,
        i.e., `new_time = func(old_time)`.

    See Also
    --------
    :func:`muspy.adjust_resolution` : Adjust the resolution and the timing
      of time-stamped objects.

    Note
    ----
    The resolution are left unchanged.

    """
    return obj.adjust_time(func=func)


def append(obj1: ComplexBase, obj2) -> ComplexBase:
    """Append an object to the correseponding list.

    - If `obj1` is of type :class:`muspy.Music`, `obj2` can be
      :class:`muspy.KeySignature`, :class:`muspy.TimeSignature`,
      :class:`muspy.Lyric`, :class:`muspy.Annotation` or
      :class:`muspy.Track`.
    - If `obj1` is of type :class:`muspy.Track`, `obj2` can be
      :class:`muspy.Note`, :class:`muspy.Lyric` or
      :class:`muspy.Annotation`.
    - If `obj1` is of type :class:`muspy.Timing`, `obj2` can be
      :class:`muspy.Tempo`.

    Parameters
    ----------
    obj1 : :class:`muspy.Music`, :class:`muspy.Track` or
           :class:`muspy.Tempo` object
        Object to which `obj2` to append.
    obj2 : MusPy objects (see below)
        Object to be appended to `obj1`.

    """
    return obj1.append(obj2)


def clip(
    obj: Union[Music, Track, Note], lower: int = 0, upper: int = 127,
) -> Union[Music, Track, Note]:
    """Clip the velocity of each note.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or :class:`muspy.Note`
          object
        Object to clip.
    lower : int or float, optional
        Lower bound. Defaults to 0.
    upper : int or float, optional
        Upper bound. Defaults to 127.

    """
    return obj.clip(lower=lower, upper=upper)


def get_end_time(obj: Union[Music, Track], is_sorted: bool = False) -> int:
    """Return the end time, i.e., the time of the last event in all tracks.

    This includes tempos, key signatures, time signatures, notes offsets,
        lyrics and annotations.

    Parameters
    ----------
    obj : :class:`muspy.Music` or :class:`muspy.Track` object
        Object to inspect.
    is_sorted : bool
        Whether all the list attributes are sorted. Defaults to False.

    """
    return obj.get_end_time(is_sorted=is_sorted)


def get_real_end_time(music: Music, is_sorted: bool = False) -> float:
    """Return the end time in realtime.

    This includes tempos, key signatures, time signatures, notes offsets,
        lyrics and annotations. Assume 120 qpm (quarter notes per minute) if no
        tempo information is available.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Object to inspect.
    is_sorted : bool
        Whether all the list attributes are sorted. Defaults to False.

    """
    return music.get_real_end_time(is_sorted=is_sorted)


def remove_duplicate(obj: ComplexBase) -> ComplexBase:
    """Remove duplicate change events.

    Parameters
    ----------
    obj : :class:`muspy.Music` object
        Object to process.

    """
    return obj.remove_duplicate()


def sort(obj: ComplexBase) -> ComplexBase:
    """Sort all the time-stamped objects with respect to event time.

    - If a :class:`muspy.Music` is given, this will sort key signatures,
      time signatures, lyrics and annotations, along with notes, lyrics and
      annotations for each track.
    - If a :class:`muspy.Track` is given, this will sort notes, lyrics and
      annotations.

    Parameters
    ----------
    obj : :class:`muspy.ComplexBase` object
        Object to sort.

    """
    return obj.sort()


def to_ordered_dict(obj: Base, ignore_null: bool = True) -> OrderedDict:
    """Return an OrderedDict converted from a Music object.

    Parameters
    ----------
    obj : :class:`muspy.Base` object
        MusPy object to convert.

    Returns
    -------
    OrderedDict
        Converted OrderedDict.

    """
    return obj.to_ordered_dict(ignore_null)


def transpose(
    obj: Union[Music, Track, Note], semitone: int
) -> Union[Music, Track, Note]:
    """Transpose all the notes by a number of semitones.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or :class:`muspy.Note`
    object
        Object to transpose.
    semitone : int
        The number of semitones to transpose the notes. A positive value
        raises the pitches, while a negative value lowers the pitches.

    """
    return obj.transpose(semitone=semitone)
