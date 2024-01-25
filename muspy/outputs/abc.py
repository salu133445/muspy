"""ABC output interface."""
from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import copy
from fractions import Fraction
from math import floor
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from music21.pitch import Pitch

from ..classes import Barline, Base

if TYPE_CHECKING:
    from ..classes import Chord, KeySignature, Note, Tempo, TimeSignature
    from ..music import Music


class _ABCTrackElement(ABC):
    """
    Base class for wrappers around MusPy classes.
    Handles converting elements of the music track to ABC notation and
    ordering them in it.
    """

    PRIORITY = 0
    # Whether element takes whole line in .abc file. Characteristic for
    # fields setting parameters of music such as "K:" or "M:"
    TAKES_LINE = False

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

    def __str__(self):
        if self.TAKES_LINE:
            return f"\n{self._to_str()}\n"
        return self._to_str()

    @abstractmethod
    def _to_str(self) -> str:
        pass


class _ABCTimeSignature(_ABCTrackElement):
    PRIORITY = 1
    TAKES_LINE = True

    def __init__(self, represented: "TimeSignature"):
        self.represented: "TimeSignature"
        super().__init__(represented)

    def _to_str(self):
        numerator = self.represented.numerator
        denominator = self.represented.denominator
        if numerator == 4 and denominator == 4:
            meter = "M: C"  # common time
        elif numerator == 2 and denominator == 2:
            meter = "M: C|"  # cut time
        else:
            meter = f"M: {numerator}/{denominator}"
        length = f"L: 1/{denominator}"
        return meter + "\n" + length


class _ABCTempo(_ABCTrackElement):
    PRIORITY = 2
    TAKES_LINE = True

    def __init__(self, represented: "Tempo"):
        self.represented: "Tempo"
        super().__init__(represented)

    def _to_str(self):
        return f"Q: {int(self.represented.qpm)}"


class _ABCKeySignature(_ABCTrackElement):
    PRIORITY = 3
    TAKES_LINE = True

    def __init__(self, represented: "KeySignature"):
        self.represented: "KeySignature"
        super().__init__(represented)

    def _to_str(self):
        note = Pitch(self.represented.root)
        mode = self.represented.mode
        if mode is None:
            return f"K:{note.name}"
        return f"K:{note.name}{mode}"


class _ABCBarline(_ABCTrackElement):
    PRIORITY = 4

    def __init__(self, represented: "Barline"):
        self.represented: "Barline"
        super().__init__(represented)
        self.started_repeats = 0
        self.ended_repeats = 0
        self.ended_line = False
        self.breaks_line = False

    def _to_str(self):
        if self.started_repeats > 0 and self.ended_repeats > 0:
            return " {0}|{1}|{2} ".format(
                ":" * self.ended_repeats,
                "\n" if self.breaks_line else "",
                ":" * self.started_repeats,
            )
        else:
            return " {0}|{1}{2} {3}".format(
                ":" * self.ended_repeats,
                ":" * self.started_repeats,
                "]" * self.ended_line,
                "\n" if self.breaks_line else "",
            )

    @staticmethod
    def mark_repeats(
        start: "_ABCBarline", end: "_ABCBarline", repeat_count: int = 1
    ):
        start.started_repeats += repeat_count
        end.ended_repeats += repeat_count


class _ABCSymbol(_ABCTrackElement):
    PRIORITY = 5

    def __init__(
        self, represented: "Base", music: "Music", tie: "bool" = False
    ):
        self.represented: "Base"
        self.tie = tie
        super().__init__(represented)
        duration_in_quarters = self.represented.duration / music.resolution
        # denominator marks standard note length: 2-half note, 4-quarter,
        # 8-eighth, etc.
        time_signatures = [
            time_sig
            for time_sig in music.time_signatures
            if time_sig.time <= self.represented.time
        ]
        quarter_to_unit_length = time_signatures[-1].denominator / 4
        self._length = Fraction(
            duration_in_quarters * quarter_to_unit_length
        ).limit_denominator()

    def _length_suffix(self):
        note_lenght_str = ""
        if self._length.numerator != 1:
            note_lenght_str += str(self._length.numerator)
        if self._length.denominator != 1:
            note_lenght_str += "/" + str(self._length.denominator)
        return note_lenght_str


class _ABCNote(_ABCSymbol):
    def __init__(
        self, represented: "Note", music: "Music", tie: "bool" = False
    ):
        self.represented: "Note"
        super().__init__(represented, music, tie)

    def _to_str(self):
        return (
            self._octave_adjusted_note()
            + self._length_suffix()
            + "-" * self.tie
        )

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


class _ABCChord(_ABCSymbol):
    def __init__(
        self, represented: "Chord", music: "Music", tie: "bool" = False
    ):
        self.represented: "Chord"
        super().__init__(represented, music, tie)

    def _to_str(self):
        return "[" + self.print_notes() + "-" * self.tie + "]"

    def _octave_adjusted_note(self, pitch_numeric):
        pitch = Pitch(midi=pitch_numeric)
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

    def print_notes(self):
        string = ""
        for pitch in self.represented.pitches:
            string += self._octave_adjusted_note(pitch)
            string += self._length_suffix()
        return string


class Rest(Base):
    """A container for rests.

    Attributes
    ----------
    time : int
        Time of the rest, in time steps.
    duration: int
        Duration of the rest, in time steps.
    """

    _attributes = OrderedDict([("time", int), ("duration", int)])

    def __init__(self, time: int, duration: int):
        self.time = time
        self.duration = duration


class _ABCRest(_ABCSymbol):
    def __init__(
        self, represented: "Rest", music: "Music", tie: "bool" = False
    ):
        self.represented: "Rest"
        super().__init__(represented, music, tie)

    def _to_str(self):
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
        self._sections_borders: list[_ABCBarline] = []
        self._sections_occurences: list[int] = []
        self._sections: list[list[_ABCNote]] = []
        self.track = track

    @staticmethod
    def _enclose(track: "list[_ABCBarline|_ABCNote]"):
        """
        Ensure that `track` is enclosed by barlines in order to make it
        possible to mark repetitions involving either first or last bar of
        track.
        """
        if len(track) > 0:
            if type(track[0]) != _ABCBarline:
                barline = Barline(getattr(track[0].represented, "time"))
                track.insert(0, _ABCBarline(barline))
            if type(track[-1]) != _ABCBarline:
                barline = Barline(getattr(track[-1].represented, "time") + 1)
                track.append(_ABCBarline(barline))
        return track

    def _disassemble(self):
        """
        Break track into sequences of notes and separating them barlines.
        Prepare a counter for number of occurences for each sequence of notes.
        """
        last_barline_index = 0
        enclosed = self._enclose(self.track)
        self._sections_borders = [enclosed[0]]
        self._sections_occurences = []
        self._sections = []
        for i in range(1, len(enclosed)):
            element = enclosed[i]
            if type(element) == _ABCBarline:
                self._sections_borders.append(element)
                self._sections_occurences.append(1)
                self._sections.append(enclosed[last_barline_index + 1 : i])
                last_barline_index = i

    def _assemble(self):
        """
        Reassemble track from sections and separating them barlines.
        Mark repetitions of sections based on corresponding counters.
        """
        track = [self._sections_borders[0]]
        for occurences, section, closing_barline in zip(
            self._sections_occurences,
            self._sections,
            self._sections_borders[1:],
        ):
            opening_barline = track[-1]
            _ABCBarline.mark_repeats(
                opening_barline, closing_barline, occurences - 1
            )
            track += section + [closing_barline]
        return track

    def _get_section(self, index: int, n: int):
        """
        Get section of track starting with subsection at `index` and
        containing `n` next subsections. Barlines separating subsections are
        incorporated into retrieved section.
        """
        section = [*self._sections[index]]
        for i in range(1, n):
            section += [self._sections_borders[index + i]] + self._sections[
                index + i
            ]
        return section

    def _find_repeat(self, repeat_length: int):
        """
        Looks for the first repeat of given length in track

        Parameters
        ----------
        repeat_length : int
            number of sections to include in repeat

        Returns
        -------
        tuple[int, int]
            Index of section that starts repeating fragment and number of
            repetitions
        """
        sections_count = len(self._sections)
        repeat_count = 0
        for start in range(sections_count - 2 * repeat_length + 1):
            # ABC format has no syntax for nested repeats
            occurences = self._sections_occurences[
                start : start + repeat_length
            ]
            if any([n != 1 for n in occurences]):
                continue
            base = self._get_section(start, repeat_length)
            for repeat_start in range(
                start + repeat_length,
                sections_count - repeat_length + 1,
                repeat_length,
            ):
                repeat = self._get_section(repeat_start, repeat_length)
                if base == repeat:
                    repeat_count += 1
                    # ABC reader can't handle markings for more than 2 repeats
                    # (|: notes and bars :|)
                    break
                else:
                    break
            if repeat_count > 0:
                return start, repeat_count
        return 0, 0

    def _remove_repeat(
        self, index: int, repeat_length: int, repeat_count: int
    ):
        """
        Replace a block of `repeat_count` repeats each containing
        `repeat_length` sections starting at 'index' with concatenated
        sections from original and mark its occurence count.
        """
        concatenated = self._get_section(index, repeat_length)
        # include original
        repeated_sections_count = repeat_length * (repeat_count + 1)
        self._sections_borders = (
            self._sections_borders[: index + 1]
            + self._sections_borders[index + repeated_sections_count :]
        )
        self._sections_occurences = (
            self._sections_occurences[: index + 1]
            + self._sections_occurences[index + repeated_sections_count :]
        )
        self._sections = (
            self._sections[: index + 1]
            + self._sections[index + repeated_sections_count :]
        )
        self._sections_occurences[index] = repeat_count + 1
        self._sections[index] = concatenated

    def _compact(self):
        """
        Detect consecutive repetitions of track sections. Remove repeated
        sections and mark occurence counts of originals.
        """
        repeat_length = floor(len(self._sections) / 2)
        while repeat_length > 0:
            start, repeat_count = self._find_repeat(repeat_length)
            while repeat_count > 0:
                self._remove_repeat(start, repeat_length, repeat_count)
                repeat_length = floor(len(self._sections) / 2)
                if repeat_length < 1:
                    break
                start, repeat_count = self._find_repeat(repeat_length)
            repeat_length -= 1

    def compact(self):
        """
        Detect repetitions in track contained by object. Mark repeats of
        sections of track on barlines enclosing them and remove repeated
        elements.
        """
        if len(self.track) == 0:
            return self.track
        self._disassemble()
        self._compact()
        return self._assemble()


def break_lines(track: "list[_ABCTrackElement]", bars_per_line: int = 4):
    i = 0
    bar_counter = 0
    while i < len(track):
        element = track[i]
        if type(element) == _ABCBarline:
            bar_counter = (bar_counter + 1) % bars_per_line
            if bar_counter == 0:
                element.breaks_line = True
        elif element.TAKES_LINE:
            bar_counter = 0
            i += 1  # Skip opening barline of the first bar
        i += 1


def mark_repetitions(track: "list[_ABCTrackElement]"):
    same_key_fragments: list[list[_ABCTrackElement]] = []
    changes = []
    last_change_index = -1
    for i in range(len(track)):
        if track[i].TAKES_LINE:
            same_key_fragments.append(track[last_change_index + 1 : i])
            changes.append(track[i])
            last_change_index = i
    same_key_fragments.append(track[last_change_index + 1 : len(track)])

    for i in range(len(same_key_fragments)):
        same_key_fragments[i] = _TrackCompactor(
            same_key_fragments[i]
        ).compact()

    new_track = same_key_fragments[0]
    for i in range(len(changes)):
        new_track.append(changes[i])
        new_track += same_key_fragments[i + 1]
    return new_track


def find_rests(notes: "_ABCSymbol", music: "Music"):
    rests = []
    prev_note = notes[0]
    for note in notes[1:]:
        gap_duration = note.represented.time - (
            prev_note.represented.time + prev_note.represented.duration
        )
        if gap_duration > 0:
            rests.append(
                _ABCRest(
                    Rest(
                        prev_note.represented.time
                        + prev_note.represented.duration,
                        gap_duration,
                    ),
                    music,
                )
            )
        prev_note = note
    return rests


def split_symbol(
    bar_time: int, el_prev: "_ABCSymbol", end: int, music: "Music"
):
    new_el1 = copy(el_prev.represented)
    new_el1.duration = bar_time - el_prev.represented.time
    new_el1 = type(el_prev)(new_el1, music, True)

    new_el2 = copy(el_prev.represented)
    new_el2.duration = end - bar_time
    new_el2.time = bar_time
    new_el2 = type(el_prev)(new_el2, music, False)
    return new_el1, new_el2


def adjust_symbol_duration_over_bars(
    track: "list[_ABCTrackElement]", music: "Music"
):
    track_new = []
    el_prev = track[0]
    if isinstance(el_prev, _ABCTimeSignature):
        bar_lenght = (
            4
            / el_prev.represented.denominator
            * el_prev.represented.numerator
            * music.resolution
        )

    for el in track[1:]:
        if isinstance(el, _ABCTimeSignature):
            bar_lenght = (
                4
                / el.represented.denominator
                * el.represented.numerator
                * music.resolution
            )
        if isinstance(el, _ABCBarline) and isinstance(el_prev, _ABCSymbol):
            end = el_prev.represented.time + el_prev.represented.duration
            if end > el.represented.time:
                # symbol lasts several bars
                new_el1, new_el2 = split_symbol(
                    el.represented.time, el_prev, end, music
                )
                track_new.append(new_el1)
                # symbol lasts more than 2 bars
                while new_el2.represented.duration > bar_lenght:
                    end = (
                        new_el2.represented.time + new_el2.represented.duration
                    )
                    new_el3, new_el2 = split_symbol(
                        el.represented.time + bar_lenght, new_el2, end, music
                    )
                    track_new.append(new_el3)
                track_new.append(new_el2)
            else:
                track_new.append(el_prev)
        else:
            track_new.append(el_prev)
        el_prev = el

    track_new.append(track[-1])

    return track_new


def generate_note_body(
    music: "Music", compact_repeats: bool = True, **kwargs
) -> "list[str]":
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    time_sigs = [
        _ABCTimeSignature(time_sig) for time_sig in music.time_signatures
    ]
    time_sigs = remove_consecutive_repeats(time_sigs)

    tempos = [_ABCTempo(tempo) for tempo in music.tempos]
    tempos = remove_consecutive_repeats(tempos)

    keys = [_ABCKeySignature(key) for key in music.key_signatures]
    keys = remove_consecutive_repeats(keys)

    barlines = [_ABCBarline(barline) for barline in music.barlines]
    notes_chords = []
    rests = []
    if music.tracks:
        notes = [_ABCNote(note, music) for note in music.tracks[0].notes]
        chords = [_ABCChord(chord, music) for chord in music.tracks[0].chords]

        notes_chords = notes + chords
        notes_chords.sort()
        rests = find_rests(notes_chords, music)

    track = time_sigs + tempos + keys + barlines + notes_chords + rests
    track.sort()

    track = adjust_symbol_duration_over_bars(track, music)
    track.sort()

    if compact_repeats:
        track = mark_repetitions(track)

    break_lines(track, **kwargs)

    ended_barline = _ABCBarline(Barline(track[-1].represented.time + 1))
    ended_barline.ended_line = True
    track += [ended_barline]

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
