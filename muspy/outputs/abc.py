"""ABC output interface."""
from abc import ABC, abstractmethod
from math import floor
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from music21.pitch import Pitch

from ..classes import Barline

if TYPE_CHECKING:
    from ..base import Base
    from ..classes import KeySignature, Note
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
        self.started_repeats = 0
        self.ended_repeats = 0

    def __str__(self):
        return (
            " "
            + ":" * self.ended_repeats
            + "|"
            + ":" * self.started_repeats
            + " "
        )

    @staticmethod
    def mark_repeats(
        start: "_ABCBarline", end: "_ABCBarline", repeat_count: int = 1
    ):
        start.started_repeats += repeat_count
        end.ended_repeats += repeat_count


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


class _TrackCompactor:
    """Compacts tracks by detecting repeats of bars"""

    def __init__(self, track: "list[_ABCBarline|_ABCNote]"):
        self.compacted = track
        self._barlines_indices: list[int] = []
        self._bars_count = -1

    def _enclose(self):
        if len(self.compacted) > 0:
            if type(self.compacted[0]) != _ABCBarline:
                barline = Barline(
                    getattr(self.compacted[0].represented, "time")
                )
                self.compacted.insert(0, _ABCBarline(barline))
            if type(self.compacted[-1]) != _ABCBarline:
                barline = Barline(
                    getattr(self.compacted[-1].represented, "time") + 1
                )
                self.compacted.append(_ABCBarline(barline))

    def _detect_barlines(self):
        for i in range(len(self.compacted)):
            if type(self.compacted[i]) == _ABCBarline:
                self._barlines_indices.append(i)
        self._bars_count = len(self._barlines_indices) - 1

    def _get_n_bars(self, start_index: int, n: int):
        start = self._barlines_indices[start_index]
        # include closing barline
        end = self._barlines_indices[start_index + n] + 1
        return self.compacted[start:end]

    @staticmethod
    def _equal_bars(a, b):
        if len(a) != len(b):
            return False
        for a_element, b_element in zip(a, b):
            if a_element != b_element:
                return False
        # No notation for nested repeats
        if (
            a[0].started_repeats != 0
            or b[0].started_repeats != 0
            or a[-1].ended_repeats != 0
            or b[-1].ended_repeats != 0
        ):
            return False

        return True

    def _erase_n_bars(self, start_index: int, n: int):
        start = self._barlines_indices[start_index]
        end = self._barlines_indices[start_index + n]
        erased_elements = end - start
        self.compacted = self.compacted[:start] + self.compacted[end:]
        for i in range(start_index + n, len(self._barlines_indices)):
            self._barlines_indices[i] -= erased_elements
        self._barlines_indices = (
            self._barlines_indices[:start_index]
            + self._barlines_indices[start_index + n :]
        )
        self._bars_count -= n

    def _mark_repeat(
        self, start_index: int, repeat_length: int, repeat_count: int
    ):
        self._erase_n_bars(
            start_index + repeat_length, repeat_length * repeat_count
        )
        start_barline = self.compacted[self._barlines_indices[start_index]]
        end_barline = self.compacted[
            self._barlines_indices[start_index + repeat_length]
        ]
        _ABCBarline.mark_repeats(
            start_barline,
            end_barline,
            repeat_count,
        )

    def _compact(self):
        found_repeat = False
        for repeat_length in range(1, floor(self._bars_count / 2)):
            for start in range(self._bars_count + 1 - 2 * repeat_length):
                repeat_count = 0
                base = self._get_n_bars(start, repeat_length)
                for repeat_start in range(
                    start + repeat_length,
                    self._bars_count + 1 - repeat_length,
                    repeat_length,
                ):
                    repeat = self._get_n_bars(repeat_start, repeat_length)
                    if self._equal_bars(base, repeat):
                        repeat_count += 1
                        found_repeat = True
                    else:
                        break
                if repeat_count > 0:
                    self._mark_repeat(start, repeat_length, repeat_count)
                    break
            if found_repeat:
                break
        return found_repeat

    def compact(self):
        self._enclose()
        self._detect_barlines()
        while self._compact():
            pass
        return self.compacted


def mark_repetitions(track: "list[_ABCTrackElement]"):
    same_key_fragments: list[list[_ABCTrackElement]] = []
    key_changes: list[_ABCKeySignature] = []
    last_key_change_index = -1
    for i in range(len(track)):
        if type(track[i]) == _ABCKeySignature:
            same_key_fragments.append(track[last_key_change_index + 1 : i])
            key_changes.append(track[i])
            last_key_change_index = i
    same_key_fragments.append(track[last_key_change_index + 1 : len(track)])

    for i in range(len(same_key_fragments)):
        same_key_fragments[i] = _TrackCompactor(
            same_key_fragments[i]
        ).compact()

    new_track = same_key_fragments[0]
    for i in range(len(key_changes)):
        new_track.append(key_changes[i])
        new_track += same_key_fragments[i + 1]
    return new_track


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

    track = keys + barlines + notes
    track.sort()
    track = mark_repetitions(track)

    note_str = "".join(str(abc) for abc in track)
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

    with open(path, "w", encoding="utf-8") as file:
        for line in file_lines:
            file.write(f"{line}\n")
