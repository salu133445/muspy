"""Utility functions."""
from collections import OrderedDict
from typing import Dict, List, Tuple

import yaml

NOTE_MAP: Dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

CIRCLE_OF_FIFTHS: List[Tuple[int, str]] = [
    (4, "Fb"),
    (11, "Cb"),
    (6, "Gb"),
    (1, "Db"),
    (8, "Ab"),
    (3, "Eb"),
    (10, "Bb"),
    (5, "F"),  # Lydian
    (0, "C"),  # Major/Ionian
    (7, "G"),  # Mixolydian
    (2, "D"),  # Dorian
    (9, "A"),  # Minor/Aeolian
    (4, "E"),  # Phrygian
    (11, "B"),  # Locrian
    (6, "F#"),
    (1, "C#"),
    (8, "G#"),
    (3, "D#"),
    (10, "A#"),
    (5, "E#"),
    (0, "B#"),
]

MODE_CENTERS = {
    "major": 8,
    "minor": 11,
    "lydian": 7,
    "ionian": 8,
    "mixolydian": 9,
    "dorian": 10,
    "aeolian": 11,
    "phrygian": 12,
    "locrian": 13,
}

NOTE_TYPE_MAP: Dict[str, float] = {
    "1024th": 0.00390625,
    "512th": 0.0078125,
    "256th": 0.015625,
    "128th": 0.03125,
    "64th": 0.0625,
    "32nd": 0.125,
    "16th": 0.25,
    "eighth": 0.5,
    "quarter": 1.0,
    "half": 2.0,
    "whole": 4.0,
    "breve": 8.0,
    "long": 16.0,
    "maxima": 32.0,
}

TONAL_PITCH_CLASSES = {
    -1: "Fbb",
    0: "Cbb",
    1: "Gbb",
    2: "Dbb",
    3: "Abb",
    4: "Ebb",
    5: "Bbb",
    6: "Fb",
    7: "Cb",
    8: "Gb",
    9: "Db",
    10: "Ab",
    11: "Eb",
    12: "Bb",
    13: "F",
    14: "C",
    15: "G",
    16: "D",
    17: "A",
    18: "E",
    19: "B",
    20: "F#",
    21: "C#",
    22: "G#",
    23: "D#",
    24: "A#",
    25: "E#",
    26: "B#",
    27: "F##",
    28: "C##",
    29: "G##",
    30: "D##",
    31: "A##",
    32: "E##",
    33: "B##",
}


def note_str_to_note_num(note_str: str):
    """Return the note number of a note string.

    The regular expression for the note string is `[A-G][#b]*`. The base
    note must be capitalized. There can be multiple accidentals, where
    '#' denotes a sharp and 'b' denotes a flat. Some examples include
    'C'->0, 'D#'->3, 'Eb'->3.

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


class OrderedDumper(yaml.SafeDumper):
    """A dumper that supports OrderedDict."""


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


OrderedDumper.add_representer(OrderedDict, _dict_representer)


def yaml_dump(
    data, Dumper=None, allow_unicode: bool = True, **kwargs
):  # pylint: disable=invalid-name
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """
    if Dumper is None:
        Dumper = OrderedDumper
    return yaml.dump(
        data, Dumper=Dumper, allow_unicode=allow_unicode, **kwargs
    )
