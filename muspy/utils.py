"""Utilities."""
from bisect import bisect_left, bisect_right
from collections import OrderedDict
from typing import List, Union

from .classes import DEFAULT_BEAT_RESOLUTION, Note, Tempo, Track
from .music import Music


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


def append(
    obj1: Union[Music, Track], obj2,
):
    """Append an object to the correseponding list.

    If `obj1` is of type :class:`muspy.Music`, `obj2` can be
    :class:`muspy.TimeSignature`, :class:`muspy.KeySignature`,
    :class:`muspy.Tempo`, :class:`muspy.Lyric`, :class:`muspy.Annotation`
    or :class:`muspy.Track`. If `obj1` is of type :class:`muspy.Track`,
    `obj2` can be :class:`muspy.Note`, :class:`muspy.Lyric` or
    :class:`muspy.Annotation`.

    Parameters
    ----------
    obj : MusPy objects (see below)
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


def quantize_absolute_timing(
    music: Music, step: float, beat_resolution: int = DEFAULT_BEAT_RESOLUTION,
):
    """Quantize all the time-stamped objects, assuming absolute timing.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Object to be quantized.
    step : int or float
        Length of quantization step, in seconds.
    beat_resolution : int
        Time steps per beat.

    """
    if music.timing.is_symbolic_timing:
        return

    bpm = 60 / (step * beat_resolution)
    music.tempos = [Tempo(0.0, bpm)]

    for track in music.tracks:
        for note in track.notes:
            note.start = round(note.start / step)
            note.end = round(note.end / step)
    music.timing.is_symbolic_timing = True


def quantize_by_beats(music: Music, beats: List[float]):
    """Quantize all the symbolic-time-stamped objects.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Object to be quantized.
    step : np.ndarray or list of int or float
        Length of quantization step, in seconds.

    """
    if music.timing.is_symbolic_timing:
        return
    beats = [float(beat) for beat in beats]
    for track in music.tracks:
        for note in track.notes:
            note.start = bisect_left(beats, note.start)
            note.end = bisect_right(beats, note.end)
    music.timing.is_symbolic_timing = True


def quantize(
    music: Music, step: float, beat_resolution: int = DEFAULT_BEAT_RESOLUTION,
):
    """Quantize all the time-stamped objects."""
    if not music.timing.is_symbolic_timing:
        quantize_absolute_timing(music, step, beat_resolution)

    # if music.down_beats:
    # if not music.time_signature_changes:
    #     raise ValueError("")
    # first_beat_time = min(
    #     music.time_signature_changes, key=lambda x: x["time"]
    # )
