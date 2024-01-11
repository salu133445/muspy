"""ABC output interface."""
from abc import ABC, abstractmethod
from math import floor
from pathlib import Path
from typing import TYPE_CHECKING, List, Union
from collections import OrderedDict
from copy import copy

from music21.pitch import Pitch

from ..classes import Barline, Base

if TYPE_CHECKING:
    from ..base import Base
    from ..classes import Tempo, TimeSignature, KeySignature, Note
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


class _ABCTimeSignature(_ABCTrackElement):
    PRIORITY = 1

    def __init__(self, represented: "TimeSignature"):
        self.represented: "TimeSignature"
        super().__init__(represented)

    def __str__(self):
        numerator = self.represented.numerator
        denominator = self.represented.denominator
        if numerator == 4 and denominator == 4:
            meter = "M: C"  # common time
        elif numerator == 2 and denominator == 2:
            meter = "M: C|"  # cut time
        else:
            meter = f"\nM: {numerator}/{denominator}"
        return meter + f"\nL: 1/{denominator}"


class _ABCTempo(_ABCTrackElement):
    PRIORITY = 2

    def __init__(self, represented: "Tempo"):
        self.represented: "Tempo"
        super().__init__(represented)

    def __str__(self):
        tempo = f"\nQ: {int(self.represented.qpm)}"
        return tempo


class _ABCKeySignature(_ABCTrackElement):
    PRIORITY = 3

    def __init__(self, represented: "KeySignature"):
        self.represented: "KeySignature"
        super().__init__(represented)

    def __str__(self):
        note = Pitch(self.represented.root)
        mode = self.represented.mode
        if mode is None:
            key = f"\nK:{note.name}\n"
        else:
            key = f"\nK:{note.name}{mode}\n"
        return key


class _ABCBarline(_ABCTrackElement):
    PRIORITY = 4

    def __init__(self, represented: "Barline"):
        self.represented: "Barline"
        super().__init__(represented)
        self.started_repeats = 0
        self.ended_repeats = 0
        self.breaks_line = False

    def __str__(self):
        barline = (
            " "
            + ":" * self.ended_repeats
            + "|"
            + ":" * self.started_repeats
            + " "
        )
        if self.breaks_line:
            barline += "\n"
        return barline

    @staticmethod
    def mark_repeats(
        start: "_ABCBarline", end: "_ABCBarline", repeat_count: int = 1
    ):
        start.started_repeats += repeat_count
        end.ended_repeats += repeat_count


class _ABCSymbol(_ABCTrackElement):
    PRIORITY = 5

    def __init__(self, represented: "Base", music: "Music", tie: "bool" = False):
        self.represented: "Base"
        self.tie = tie
        super().__init__(represented)
        duration_in_quarters = self.represented.duration / music.resolution
        # denominator marks standard note length: 2-half note, 4-quarter,
        # 8-eighth, etc.
        time_signatures = [time_sig for time_sig in music.time_signatures if time_sig.time <= self.represented.time]
        quarter_to_unit_length = time_signatures[-1].denominator / 4
        self._length = duration_in_quarters * quarter_to_unit_length

    def _length_suffix(self):
        numerator, denominator = self._length.as_integer_ratio()
        note_lenght_str = ""
        if numerator != 1:
            note_lenght_str += str(numerator)
        if denominator != 1:
            note_lenght_str += "/" + str(denominator)
        return note_lenght_str

class _ABCNote(_ABCSymbol):

    def __init__(self, represented: "Note", music: "Music", tie: "bool" = False):
        self.represented: "Note"
        super().__init__(represented, music, tie)

    def __str__(self):
        return self._octave_adjusted_note() + self._length_suffix() + '-'*self.tie

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

class Rest(Base):
    """A container for rests.

    Attributes
    ----------
    time : int
        Time of the rest, in time steps.
    duration: int
        Duration of the rest, in time steps.
    """

    _attributes = OrderedDict(
        [
            ("time", int),
            ("duration", int)
        ]
    )

    def __init__(self, time: int, duration: int):
        self.time = time
        self.duration = duration

class _ABCRest(_ABCSymbol):

    def __init__(self, represented: "Rest", music: "Music", tie: "bool" = False):
        self.represented: "Rest"
        super().__init__(represented, music, tie)

    def __str__(self):
        return "z" + self._length_suffix()


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
        for repeat_length in range(1, floor(self._bars_count / 2) + 1):
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


def break_lines(track: "list[_ABCTrackElement]", bars_per_line: int = 4):
    i = 0
    bar_counter = 0
    while i < len(track):
        element = track[i]
        if type(element) == _ABCBarline:
            bar_counter = (bar_counter + 1) % bars_per_line
            if bar_counter == 0:
                element.breaks_line = True
        elif type(element) == _ABCKeySignature:
            bar_counter = 0
            i += 1  # Skip opening barline of the first bar
        i += 1
    bar_counter = 0
    for element in track[1:]:
        if type(element) == _ABCBarline:
            bar_counter = (bar_counter + 1) % bars_per_line


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

def find_rests(music: "Music"):
    rests = []
    prev_note = music.tracks[0].notes[0]
    for note in music.tracks[0].notes[1:]:
        gap_duration = note.time - (prev_note.time + prev_note.duration)
        if gap_duration > 0:
            rests.append(_ABCRest(Rest(prev_note.time + prev_note.duration, gap_duration), music))
        prev_note = note
    return rests

def split_symbol(el: "_ABCBarline", el_prev: "_ABCSymbol", end: int, music: "Music"):
    new_el1 = copy(el_prev.represented)
    new_el1.duration = el.represented.time - el_prev.represented.time
    new_el1 = type(el_prev)(new_el1, music, True)

    new_el2 = copy(el_prev.represented)
    new_el2.duration = end - el.represented.time
    new_el2.time = el.represented.time
    new_el2 = type(el_prev)(new_el2, music, False)
    return new_el1, new_el2

def adjust_symbol_duration_over_bars(track: "list[_ABCTrackElement]", music: "Music"):
    track_new = []
    el_prev = track[0]

    for el in track[1:]:
        if isinstance(el, _ABCBarline) and isinstance(el_prev, _ABCSymbol):
            end = el_prev.represented.time + el_prev.represented.duration
            if end > el.represented.time:
                # symbol lasts several bars
                new_el1, new_el2 = split_symbol(el, el_prev, end, music)
                track_new.append(new_el1)
                track_new.append(new_el2)
            else:
                track_new.append(el_prev)
        else:
            track_new.append(el_prev)
        el_prev = el

    track_new.append(track[-1])

    return track_new

def generate_note_body(music: "Music", compact_repeats: bool = False, **kwargs) -> "list[str]":
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    time_sigs = [_ABCTimeSignature(time_sig) for time_sig in music.time_signatures]
    time_sigs = remove_consecutive_repeats(time_sigs)

    tempos = [_ABCTempo(tempo) for tempo in music.tempos if tempo.qpm != 120]
    tempos = remove_consecutive_repeats(tempos)

    keys = [_ABCKeySignature(key) for key in music.key_signatures]
    keys = remove_consecutive_repeats(keys)

    barlines = [_ABCBarline(barline) for barline in music.barlines]
    notes = [_ABCNote(note, music) for note in music.tracks[0].notes]

    rests = find_rests(music)

    track = time_sigs + tempos + keys + barlines + notes + rests
    track.sort()

    track = adjust_symbol_duration_over_bars(track, music)
    track.sort()

    if compact_repeats:
        track = mark_repetitions(track)

    break_lines(track, **kwargs)

    track_str = "".join(str(element) for element in track)
    lines = track_str.split("\n")
    lines = list(filter(None, lines))
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip().rstrip()
    return lines


def write_abc(path: Union[str, Path], music: "Music", **kwargs):
    """Write a Music object to an ABC file.

    Parameters
    ----------
    path : str or Path
        Path to write the ABC file.
    music : :class:`muspy.Music`
        Music object to write.
    """

    file_lines = generate_header(music)
    file_lines += generate_note_body(music, **kwargs)

    with open(path, "w", encoding="utf-8") as file:
        for line in file_lines:
            file.write(f"{line}\n")
