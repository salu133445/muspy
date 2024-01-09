"""ABC output interface."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from music21.pitch import Pitch

if TYPE_CHECKING:
    from ..base import Base
    from ..classes import Barline, KeySignature, Note
    from ..music import Music


class _ABCTrackElement(ABC):
    """
    Base class for wrappers around MusPy classes.
    Handles converting elements of the music track to ABC notation and
    ordering them in it.
    """

    PRIORITY = 0

    def __init__(self, represented: "Base") -> None:
        self.represented = represented

    def __eq__(self, other: "_ABCTrackElement"):
        """
        Check if `other` represents the same set of musical data, possibly
        occuring in a different moment of music track
        """
        try:
            temp_time = getattr(other.represented, "time")
            setattr(
                other.represented, "time", getattr(self.represented, "time")
            )
            result = self.represented == other.represented
            setattr(other.represented, "time", temp_time)
        except AttributeError:
            result = self.represented == other.represented
        return result

    def __lt__(self, other: "_ABCTrackElement"):
        """
        Check if element should be written in ABC notation before `other`.
        """
        if self.represented < other.represented:
            return True
        if (
            getattr(self.represented, "time")
            == getattr(other.represented, "time")
            and self.PRIORITY < other.PRIORITY
        ):
            return True
        return False

    def __gt__(self, other: "_ABCTrackElement"):
        """
        Check if element should be written in ABC notation after `other`.
        """
        if self.represented > other.represented:
            return True
        if (
            getattr(self.represented, "time")
            == getattr(other.represented, "time")
            and self.PRIORITY > other.PRIORITY
        ):
            return True
        return False

    @abstractmethod
    def __str__(self):
        pass


class _ABCKeySignature(_ABCTrackElement):
    PRIORITY = 1

    def __init__(self, represented: "KeySignature"):
        self.represented: "KeySignature"
        super().__init__(represented)

    def __str__(self):
        note = Pitch(self.represented.root)
        mode = self.represented.mode
        return f"\nK:{note.name+mode}\n"


class _ABCBarline(_ABCTrackElement):
    PRIORITY = 2

    def __init__(self, represented: "Barline"):
        self.represented: "Barline"
        super().__init__(represented)

    def __str__(self):
        return " | "


class _ABCNote(_ABCTrackElement):
    PRIORITY = 3

    def __init__(self, represented: "Note", music: "Music"):
        self.represented: "Note"
        super().__init__(represented)
        duration_in_quarters = self.represented.duration / music.resolution
        # denominator marks standard note length: 2-half note, 4-quarter,
        # 8-eighth, etc.
        quarter_to_unit_length = music.time_signatures[0].denominator / 4
        self._length = duration_in_quarters * quarter_to_unit_length

    def __str__(self):
        return self._octave_adjusted_note() + self._length_suffix()

    def _octave_adjusted_note(self):
        pitch = Pitch(midi=self.represented.pitch)
        note = pitch.name
        if len(note) > 1:
            if note[-1] == "#":  # sharp
                note = "^" + note[0]
            elif note[-1] == "-":  # flat
                note = "_" + note[0]
        if pitch.octave <= 4:
            note = note + "," * (4 - pitch.octave)
        else:
            note = note.lower() + "'" * (pitch.octave - 5)
        return note

    def _length_suffix(self):
        numerator, denominator = self._length.as_integer_ratio()
        note_lenght_str = ""
        if numerator != 1:
            note_lenght_str += str(numerator)
        if denominator != 1:
            note_lenght_str += "/" + str(denominator)
        return note_lenght_str


def meter_and_unit(music: "Music") -> List[str]:
    """Return meter and note unit from Music object
    in abc header format.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC header.
    """
    numerator = music.time_signatures[0].numerator
    denominator = music.time_signatures[0].denominator
    if numerator == 4 and denominator == 4:
        meter = "M: C"  # common time
    elif numerator == 2 and denominator == 2:
        meter = "M: C|"  # cut time
    else:
        meter = f"M: {numerator}/{denominator}"
    return [meter, f"L: 1/{denominator}"]


def generate_header(music: "Music") -> List[str]:
    """Generate ABC header from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC header.
    """
    header_lines = ["X: 1"]

    # set filename as title if no other title
    title = music.metadata.title
    if title is None:
        title = Path(music.metadata.source_filename).stem
    header_lines.append(f"T: {title}")
    creators = music.metadata.creators
    if creators:
        header_lines.append(f"C: {','.join(creators)}")

    header_lines += meter_and_unit(music=music)
    if music.tempos[0].qpm != 120:  # tempo if is different than default 120
        header_lines.append(f"Q: {int(music.tempos[0].qpm)}")
    # note = Pitch(music.key_signatures[0].root)
    # mode = music.key_signatures[0].mode if music.key_signatures[0].mode is not None else ''
    # header_lines.append(f"K: {note.name + mode}")
    return header_lines


def remove_consecutive_repeats(list: list):
    """
    Creates a copy of `list` with consecutive repeats of values skipped.
    """
    cleared = list[:1]
    for element in list[1:]:
        if element == cleared[-1]:
            continue
        cleared.append(element)
    return cleared


def generate_note_body(music: "Music") -> str:
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    keys = [_ABCKeySignature(key) for key in music.key_signatures]
    keys = remove_consecutive_repeats(keys)

    barlines = [_ABCBarline(barline) for barline in music.barlines]
    notes = [_ABCNote(note, music) for note in music.tracks[0].notes]

    elements = keys + barlines + notes
    elements.sort()
    note_str = "".join(str(abc) for abc in elements)
    return note_str.lstrip().rstrip()


def write_abc(path: Union[str, Path], music: "Music"):
    """Write a Music object to an ABC file.

    Parameters
    ----------
    path : str or Path
        Path to write the ABC file.
    music : :class:`muspy.Music`
        Music object to write.
    """

    file_lines = generate_header(music)
    file_lines.append(generate_note_body(music))

    # TODO: catch exceptions
    with open(path, "w") as file:
        for line in file_lines:
            file.write(f"{line}\n")
