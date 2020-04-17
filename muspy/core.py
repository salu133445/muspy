"""
Core functions
==============

Core functions that can be applied to a :class:`muspy.Music` object.

"""
from collections import OrderedDict
from typing import Callable, List, Optional, Union

from .classes import Note, Timing, Track
from .music import Music

__all__ = [
    "adjust_resolution",
    "adjust_time",
    "append",
    "clip",
    "quantize",
    "remove_duplicate_changes",
    "sort",
    "to_ordered_dict",
    "transpose",
]


def adjust_resolution(
    music: Music, target: Optional[int] = None, factor: Optional[float] = None
):
    """Adjust resolution and update the timing of time-stamped objects.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy music object to be adjusted.
    target : int, optional
        Target resolution.
    factor : int or float, optional
        Factor used to adjust the resolution based on the formula:
        `new_resolution = old_resolution * factor`. For example, a factor of
        2 double the resolution, and a factor of 0.5 halve the resolution.

    """
    return music.adjust_resolution(target=target, factor=factor)


def adjust_time(obj: Union[Music, Track], func: Callable[[float], float]):
    """Adjust the timing of time-stamped objects.

    Parameters
    ----------
    obj : :class:`muspy.Music` or :class:`muspy.Track` object
        Object to be adjusted.
    func : callable
        The function used to compute the new timing from the old timing,
        i.e., `new_time = func(old_time)`.

    See Also
    --------
    :meth:`muspy.adjust_resolution`: Adjust the resolution and the timing of
    time-stamped objects.

    Note
    ----
    The resolution are left unchanged.

    """
    return obj.adjust_time(func=func)


def append(
    obj1: Union[Music, Track, Timing], obj2,
):
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
        Object to which `obj2` to be append.
    obj2 : MusPy objects (see below)
        Object to be appended to `obj1`.

    """
    return obj1.append(obj2)


def clip(
    obj: Union[Music, Track, Note], lower: float = 0, upper: float = 127,
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
    return obj.clip(lower=lower, upper=upper)


def to_ordered_dict(music: Music) -> OrderedDict:
    """Return an OrderedDict converted from a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy music object to be converted.

    Returns
    -------
    OrderedDict
        Converted OrderedDict.

    """
    return music.to_ordered_dict()


def get_end_time(
    obj: Union[Music, Track, Timing], is_sorted: bool = False
) -> float:
    """Return the time of the last event.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or
          :class:`muspy.Timing` object
        Object to be inspected.
    is_sorted : bool
        Whether all the list attributes are sorted. Defaults to False.

    """
    return obj.get_end_time(is_sorted=is_sorted)


def quantize(
    music: Music,
    resolution: int,
    beats: Optional[List[float]] = None,
    bpm: float = None,
    offset: float = 0,
):
    """Quantize the timing of time-stamped objects.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy music object to be quantized.
    resolution : int
        Time steps per beat.
    beats : list of float
        Sorted list of beat positions in ascending order, assuming no
        duplicate values.
    bpm : int or float
        Length of quantization step, in seconds.
    offset : float
        Offset of the beat pulse train, e.g., start time of the first beat.

    """
    return music.quantize(
        resolution=resolution, beats=beats, bpm=bpm, offset=offset
    )


def remove_duplicate_changes(obj: Union[Music, Timing]):
    """Remove duplicate change events.

    Parameters
    ----------
    obj : :class:`muspy.Music` or :class:`muspy.Timing` object
        Object to be processed.

    """
    return obj.remove_duplicate_changes()


def sort(obj: Union[Music, Track, Timing]):
    """Sort all the time-stamped objects with respect to event time.

    - If a :class:`muspy.Music` is given, this will sort key signatures,
      time signatures, lyrics and annotations, along with notes, lyrics and
      annotations for each track.
    - If a :class:`muspy.Track` is given, this will sort notes, lyrics and
      annotations.
    - If a :class:`muspy.Timing` is given, this will sort tempos.

    Parameters
    ----------
    obj : :class:`muspy.Music`, :class:`muspy.Track` or
          :class:`muspy.Timing` object
        Object to be sorted.

    """
    return obj.sort()


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
    return obj.transpose(semitone=semitone)
