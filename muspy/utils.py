"""Utility functions."""
from typing import Dict

NOTE_MAP: Dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


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
