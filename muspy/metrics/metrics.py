"""Evaluation metrics."""
from typing import List, Tuple

import numpy as np
from numpy import ndarray

from ..music import Music


def n_pitches_used(music: Music) -> Tuple[int, List[bool]]:
    """Return the number of unique pitches used.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to be evaluate.

    Returns
    -------
    int
        Number of unique pitch classes used.
    list of bool
        A boolean list of length 128 indicating the pitches used. If the
        i-th element is True, the MIDI note pitch i is used.

    """
    count = 0
    is_used = [False] * 128
    for track in music.tracks:
        for note in track.notes:
            if not is_used[note.pitch]:
                is_used[note.pitch] = True
                count += 1
                if count > 127:
                    break
    return count, is_used


def n_pitch_classes_used(music: Music) -> Tuple[int, List[bool]]:
    """Return the number of unique pitch classes used.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to be evaluate.

    Returns
    -------
    int
        Number of unique pitch classes used.
    list of bool
        A boolean list of length 12 indicating the pitch classes used. The
        first element corresponds to pitch A, and the last one corresponds
        to pitch G# (G sharp).

    """
    count = 0
    is_used = [False] * 12
    for track in music.tracks:
        for note in track.notes:
            chroma = note.pitch // 12
            if not is_used[chroma]:
                is_used[chroma] = True
                count += 1
                if count > 11:
                    break
    return count, is_used


def empty_beat_rate(music: Music) -> float:
    r"""Return the empty beat rate.

    The empty beat rate is defined as the ratio of the number of empty beats
    (where no pitch is played) to the number of beats.

    .. math:: empty\_beat\_rate = \frac{\# of empty beats}{\# of beats}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to be evaluate.

    Returns
    -------
    float
        Empty beat rate.

    """
    length = max(track.get_end_time() for track in music.tracks)
    total_beats = length // music.timing.resolution
    is_empty = [False] * total_beats
    count = 0
    for track in music.tracks:
        for note in track.notes:
            start = note.start // music.timing.resolution
            end = note.end // music.timing.resolution
            for beat in range(start, end + 1):
                if not is_empty[beat]:
                    is_empty[beat] = True
                    count += 1
    return count / total_beats


def polyphony(music: Music, threshold: int = 2) -> float:
    r"""Return the polyphony measure.

    The polyphony is defined as the ratio of the number of time steps where
    multiple pitches are on to the total number of time steps.

    .. math::
        polyphony = \frac{
            \# of time steps where multiple pitches are on}{\# of time steps}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to be evaluate.

    Returns
    -------
    float
        Polyphony.

    """
    length = max(track.get_end_time() for track in music.tracks)
    pianoroll = np.zeros((length, 128), bool)
    for track in music.tracks:
        for note in track.notes:
            pianoroll[note.start : note.end] = 1
    return (pianoroll.sum(1) > threshold) / len(pianoroll)


def pitch_range(music: Music) -> int:
    """Return the pitch range."""
    lowest = min(note.pitch for track in music.tracks for note in track.notes)
    highest = max(note.pitch for track in music.tracks for note in track.notes)
    return highest - lowest


def get_scale(key: int, mode: str) -> ndarray:
    """Return a scale mask for the given key."""
    if mode == "major":
        a_scale_mask = np.array([0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1], bool)
    elif mode == "minor":
        a_scale_mask = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], bool)
    else:
        raise ValueError("`mode` must be either 'major' or 'minor'.")
    return np.roll(a_scale_mask, key)


def in_scale_rate(music: Music, root: int, mode: str) -> float:
    """Return the rate of notes in a musical scale.

    In scale rate is defined as the ratio of the number of notes in a scale
    to the total number of time steps.


    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to be evaluate.
    root : int
        Root of the scale.
    mode : int
        Mode of the scale.

    Returns
    -------
    float
        In scale rate.

    """
    scale = get_scale(root, mode)
    count = 0
    in_scale_count = 0
    for track in music.tracks:
        for note in track.notes:
            count += 1
            if scale[note.pitch // 12]:
                in_scale_count += 1
    return in_scale_count / count
