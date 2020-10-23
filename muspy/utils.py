"""Utility functions."""
from typing import Dict
import numpy as np
from muspy import Tempo

NOTE_MAP: Dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def encode_tempo(tempo, total_time_step):
    """
    encode tempo at each time step
    Parameters
    ----------
    tempo : :List: List of `muspy.Tusic` object
        Tempo object to encode.
    total_time_step : :int
        the total number step of expected encode
    Returns
    -------
    ndarray, dtype=uint8, shape=(shape, 1)
        Encoded tempo.
    """
    res = np.zeros(total_time_step, dtype=np.uint8)
    if len(tempo) == 0:
        # default qpm for midi standard is 120 qpm
        tempo.append(Tempo(0, 120))
    pre = tempo[0].qpm
    if len(tempo) == 1:
        res[:] = pre
        return res

    pre = tempo[0]
    curr = tempo[1]
    i = 1
    while i < len(tempo):
        assert pre.qpm != np.nan and curr.qpm != np.nan
        if pre.time > total_time_step or curr.time > total_time_step:
            break
        curr = tempo[i]
        if curr.qpm == pre.qpm:
            i = i + 1
            continue
        # curr.qpm != pre.qpm
        start, end = pre.time, curr.time
        res[start:end] = pre.qpm
        pre = curr
        i = i + 1

    res[pre.time:] = pre.qpm
    return res


def note_str_to_note_num(note_str: str):
    """Return the note number of a note string.

    The regular expression for the note string is `[A-G][#b]*`. The base
    note must be capitalized. There can be multiple accidentals, where '#'
    denotes a sharp and 'b' denotes a flat. Some examples include 'C' -> 0,
    'D#' -> 3, 'Eb' -> 3.

    Parameters
    ----------
    note_str : str
        Note string.

    Returns
    -------
    int, 0-11
        Note number.

    """
    note_num = NOTE_MAP.get(note_str[0])
    if note_num is None:
        raise ValueError(
            f"Expect a base note from 'A' to 'G', but got :{note_str[0]}."
        )
    for alter in note_str[1:]:
        if alter == "#":
            note_num += 1
        elif alter == "b":
            note_num -= 1
        else:
            raise ValueError(
                f"Expect an accidental of '#' or 'b', but got : {alter}."
            )
    if note_num > 11 or note_num < 0:
        return note_num % 12
    return note_num
