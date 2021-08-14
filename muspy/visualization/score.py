"""Score visualization interface.

Unicode encoding for musical symbols is based on Standard Music Font
Layout (SMuFL) (see https://w3c.github.io/smufl/gitbook/).

"""
import warnings
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Rectangle
from matplotlib.text import Text

from ..base import Base
from ..classes import KeySignature, Note, Tempo, TimeSignature
from ..external import get_bravura_font_path

if TYPE_CHECKING:
    from ..music import Music


COMMON_NOTE_CODES = {
    2: "\uE1D0",  # double whole note
    1: "\uE1D2",  # whole note
    0.5: "\uE1D3",  # half note
    0.25: "\uE1D5",  # quarter note
    0.125: "\uE1D7",  # 8th note
    0.0625: "\uE1D9",  # 16th note
    0.03125: "\uE1DB",  # 32th note
    0.015625: "\uE1DD",  # 64th note
    0.0078125: "\uE1DF",  # 128th note
    0.00390625: "\uE1E1",  # 256th note
    0.001953125: "\uE1E3",  # 512th note
    0.0009765625: "\uE1E5",  # 1024th note
    # Dotted
    3: "\uE1D0 \uE1E7",
    1.5: "\uE1D2 \uE1E7",
    0.75: "\uE1D3 \uE1E7",
    0.375: "\uE1D5 \uE1E7",
    0.1875: "\uE1D7 \uE1E7",
    0.09375: "\uE1D9 \uE1E7",
    0.046875: "\uE1DB \uE1E7",
    0.0234375: "\uE1DD \uE1E7",
    0.01171875: "\uE1DF \uE1E7",
    0.005859375: "\uE1E1 \uE1E7",
    0.0029296875: "\uE1E3 \uE1E7",
    0.00146484375: "\uE1E5 \uE1E7",
    # Double dotted
    3.5: "\uE1D0 \uE1E7 \uE1E7",
    1.75: "\uE1D2 \uE1E7 \uE1E7",
    0.875: "\uE1D3 \uE1E7 \uE1E7",
    0.4375: "\uE1D5 \uE1E7 \uE1E7",
    0.21875: "\uE1D7 \uE1E7 \uE1E7",
    0.109375: "\uE1D9 \uE1E7 \uE1E7",
    0.0546875: "\uE1DB \uE1E7 \uE1E7",
    0.02734375: "\uE1DD \uE1E7 \uE1E7",
    0.013671875: "\uE1DF \uE1E7 \uE1E7",
    0.0068359375: "\uE1E1 \uE1E7 \uE1E7",
    0.00341796875: "\uE1E3 \uE1E7 \uE1E7",
    0.001708984375: "\uE1E5 \uE1E7 \uE1E7",
}


COMMON_NOTE_CODES_ALT = {
    2: "\uE1D0",  # double whole note
    1: "\uE1D2",  # whole note
    0.5: "\uE1D3",  # half note
    0.25: "\uE1D5",  # quarter note
    0.125: "\uE1D5",  # 8th note
    0.0625: "\uE1D5",  # 16th note
    0.03125: "\uE1D5",  # 32th note
    0.015625: "\uE1D5",  # 64th note
    0.0078125: "\uE1D5",  # 128th note
    0.00390625: "\uE1D5",  # 256th note
    0.001953125: "\uE1D5",  # 512th note
    0.0009765625: "\uE1D5",  # 1024th note
    # Dotted
    3: "\uE1D0 \uE1E7",
    1.5: "\uE1D2 \uE1E7",
    0.75: "\uE1D3 \uE1E7",
    0.375: "\uE1D5 \uE1E7",
    0.1875: "\uE1D5 \uE1E7",
    0.09375: "\uE1D5 \uE1E7",
    0.046875: "\uE1D5 \uE1E7",
    0.0234375: "\uE1D5 \uE1E7",
    0.01171875: "\uE1D5 \uE1E7",
    0.005859375: "\uE1D5 \uE1E7",
    0.0029296875: "\uE1D5 \uE1E7",
    0.00146484375: "\uE1D5 \uE1E7",
    # Double dotted
    3.5: "\uE1D0 \uE1E7 \uE1E7",
    1.75: "\uE1D2 \uE1E7 \uE1E7",
    0.875: "\uE1D3 \uE1E7 \uE1E7",
    0.4375: "\uE1D5 \uE1E7 \uE1E7",
    0.21875: "\uE1D5 \uE1E7 \uE1E7",
    0.109375: "\uE1D5 \uE1E7 \uE1E7",
    0.0546875: "\uE1D5 \uE1E7 \uE1E7",
    0.02734375: "\uE1D5 \uE1E7 \uE1E7",
    0.013671875: "\uE1D5 \uE1E7 \uE1E7",
    0.0068359375: "\uE1D5 \uE1E7 \uE1E7",
    0.00341796875: "\uE1D5 \uE1E7 \uE1E7",
    0.001708984375: "\uE1D5 \uE1E7 \uE1E7",
}

COMMON_REST_CODES = {
    2: "\uE4E2",  # double whole rest
    1: "\uE4E3",  # whole rest
    0.5: "\uE1E4",  # half rest
    0.25: "\uE1E5",  # quarter rest
    0.125: "\uE1E6",  # 8th rest
    0.0625: "\uE1E7",  # 16th rest
    0.03125: "\uE1E8",  # 32th rest
    0.015625: "\uE1E9",  # 64th rest
    0.0078125: "\uE1EA",  # 128th rest
    0.00390625: "\uE1EB",  # 256th rest
    0.001953125: "\uE1EC",  # 512th rest
    0.0009765625: "\uE1ED",  # 1024th rest
    # Dotted
    3: "\uE4E2 \uE1E7",
    1.5: "\uE4E3 \uE1E7",
    0.75: "\uE1E4 \uE1E7",
    0.375: "\uE1E5 \uE1E7",
    0.1875: "\uE1E6 \uE1E7",
    0.09375: "\uE1E7 \uE1E7",
    0.046875: "\uE1E8 \uE1E7",
    0.0234375: "\uE1E9 \uE1E7",
    0.01171875: "\uE1EA \uE1E7",
    0.005859375: "\uE1EB \uE1E7",
    0.0029296875: "\uE1EC \uE1E7",
    0.00146484375: "\uE1ED \uE1E7",
    # Double dotted
    3.5: "\uE4E2 \uE1E7 \uE1E7",
    1.75: "\uE4E3 \uE1E7 \uE1E7",
    0.875: "\uE1E4 \uE1E7 \uE1E7",
    0.4375: "\uE1E5 \uE1E7 \uE1E7",
    0.21875: "\uE1E6 \uE1E7 \uE1E7",
    0.109375: "\uE1E7 \uE1E7 \uE1E7",
    0.0546875: "\uE1E8 \uE1E7 \uE1E7",
    0.02734375: "\uE1E9 \uE1E7 \uE1E7",
    0.013671875: "\uE1EA \uE1E7 \uE1E7",
    0.0068359375: "\uE1EB \uE1E7 \uE1E7",
    0.00341796875: "\uE1EC \uE1E7 \uE1E7",
    0.001708984375: "\uE1ED \uE1E7 \uE1E7",
}

NOTE_CODES = [
    "\uE1D0",  # double whole note
    "\uE1D2",  # whole note
    "\uE1D3",  # half note
    "\uE1D5",  # quarter note
    "\uE1D7",  # 8th note
    "\uE1D9",  # 16th note
    "\uE1DB",  # 32th note
    "\uE1DD",  # 64th note
    "\uE1DF",  # 128th note
    "\uE1E1",  # 256th note
    "\uE1E3",  # 512th note
    "\uE1E5",  # 1024th note
]

NOTE_CODES_ALT = [
    "\uE1D0",
    "\uE1D2",
    "\uE1D3",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
    "\uE1D5",
]


def _to_compound_note_codes(note_counts) -> List[str]:
    note_codes = []
    for i, note_count in enumerate(note_counts):
        for _ in range(note_count):
            note_codes.append(NOTE_CODES[i])
    return note_codes


def _to_compound_note_codes_alt(note_counts) -> List[str]:
    note_codes = []
    for i, note_count in enumerate(note_counts):
        for _ in range(note_count):
            note_codes.append(NOTE_CODES_ALT[i])
    return note_codes


def _to_note_counts(note_value) -> List[int]:
    """Return a list of counts of notes that sum to a note value.

    For example, a note value of 1.75 will be decoposed into a whole
    note, a half note and a quarter note, respectively. The return list
    is of length 12, where the first value corresponds to the count of
    double whole notes and the last value corresponds to the count of
    1024th notes.

    """
    if note_value < 2:
        base2 = bin(int(note_value * 1024))[2:]
        return [0] * (12 - len(base2)) + [int(bit) for bit in base2]
    first_bit, remainder = divmod(note_value, 2)
    base2 = bin(int(remainder * 1024))[2:]
    return (
        [int(first_bit)]
        + [0] * (11 - len(base2))
        + [int(bit) for bit in base2]
    )


def to_note_codes(note_value) -> List[str]:
    """Return a note value as a list of note codes.

    For example, a note value of 1.75 will be decoposed into a whole
    note, a half note and a quarter note, respectively.

    """
    note_code = COMMON_NOTE_CODES.get(note_value)
    if note_code is not None:
        return [note_code]
    note_counts = _to_note_counts(note_value)
    return _to_compound_note_codes(note_counts)


def to_note_codes_alt(note_value) -> List[str]:
    """Return a note value as a list of note codes with straight beams.

    This is useful for making chords as all the notes comes with a
    straight beam. For example, a note value of 1.75 will be decomposed
    into a whole note, a half note and a quarter note, respectively.

    """
    note_code = COMMON_NOTE_CODES_ALT.get(note_value)
    if note_code is not None:
        return [note_code]
    note_counts = _to_note_counts(note_value)
    return _to_compound_note_codes_alt(note_counts)


def get_time_signature_code(number: int) -> str:
    """Return a string for a time signature number."""
    if number > 10:
        div, mod = divmod(number, 10)
        return chr(57472 + div) + chr(57472 + mod)
    return chr(57472 + number)


def get_pitch_classes(fifths: int) -> List[int]:
    """Return a list of the root note of each pitch number."""
    if fifths >= 0:
        return [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
    return [0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6]


def get_accidentals(fifths: int) -> List[Optional[int]]:
    """Return a list of the accidentals and the pitch classes."""
    if fifths >= 0:
        accidentals = [None, 1, None, 1, None, None, 1, None, 1, None, 1, None]
        if fifths > 0:
            sharps = [5, 0, 7, 2, 9, 4, 11]
            for idx in sharps[:fifths]:
                # No accidental for the sharp note
                accidentals[idx + 1] = None
                # Natural for the original note
                accidentals[idx] = 0
    elif fifths < 0:
        accidentals = [
            None,
            -1,
            None,
            -1,
            None,
            None,
            -1,
            None,
            -1,
            None,
            -1,
            None,
        ]
        flats = [11, 4, 9, 2, 7, 0, 5]
        for idx in flats[:(-fifths)]:
            # No accidental for the flat note
            accidentals[idx - 1] = None
            # Natural for the original note
            accidentals[idx] = 0

    return accidentals


class ScorePlotter:
    """A plotter that handles the score visualization.

    Attributes
    ----------
    fig : :class:`matplotlib.figure.Figure`
        Figure object to plot the score on.
    axes : :class:`matplotlib.axes.Axes`
        Axes object to plot the score on.
    resolution : int
        Time steps per quarter note.
    note_spacing : int, default: 4
        Spacing of notes.
    font_path : str or Path, optional
        Path to the music font. Defaults to the path to the downloaded
        Bravura font.
    font_scale : float, default: 140
        Font scaling factor for finetuning. The default value of 140 is
        optimized for the default Bravura font.

    """

    def __init__(
        self,
        fig: Figure,
        ax: Axes,
        resolution: int,
        note_spacing: int = None,
        font_path: Union[str, Path] = None,
        font_scale: float = None,
    ):
        self.fig = fig
        self.ax = ax
        self.resolution = resolution
        self.note_spacing = note_spacing if note_spacing is not None else 4
        if font_path is None:
            self.font_path = get_bravura_font_path()
        else:
            self.font_path = Path(font_path)
        self.font_scale = 140 if font_scale is None else font_scale

        # Check if font path exists
        if not self.font_path.exists():
            raise RuntimeError(
                "Music font not found. You could download it by "
                "`muspy.download_bravura_font()`."
            )

        # Set the axes to 1:1 aspect ratio
        self.ax.set_aspect("equal")

        # Turn off the axis
        self.ax.axis(False)

        # Initialize vertical boundaries
        self.left = 0.0
        self.right = 0.0
        self.bottom = 0.0
        self.top = 0.0

        # Initialize lists to store created objects
        self.staffs: List[Line2D] = []
        self.bar_lines: List[Line2D] = []
        self.final_bar_line = None
        self.clefs: List[Text] = []
        self.tempo_texts: List[Text] = []
        self.tempo_notes: List[Text] = []
        self.key_signatures: List[Text] = []
        self.time_signatures: List[Text] = []
        self.notes: List[Text] = []
        self.ties: List[Arc] = []

        # Initialize baseline position
        # (i.e., the y-coordinate of the first, lowest staff line)
        self._baseline = 0.0

        # Initialize horizontal position cursor
        self._pos = 0.0

        # Variables for handling notes
        self._force_new_note = True
        self._clef_offset = 0.0
        self._last_note_time = 0
        self._last_note_pos = 0.0
        self._last_note_y = 0.0
        self._splits_max = 0
        self._bottom_note_y = 0.0
        self._top_note_y = 0.0

        # Variables for handling key signatures
        self._pitch_classes = get_pitch_classes(0)
        self._accidentals = get_accidentals(0)

    def set_baseline(self, y):
        """Set baseline position (y-coordinate of first staff line)."""
        self._baseline = y
        self.top = max(self.top, self._baseline)
        self.bottom = max(self.bottom, self._baseline)
        self._bottom_note_y = self._baseline
        self._top_note_y = self._baseline + 4

    def adjust_fonts(self, scale: float = None):
        """Adjust the fonts."""
        if scale is None:
            scale = self.font_scale

        self.ax.set_xlim(self.left, self.right)
        self.ax.set_ylim(self.bottom, self.top)

        # Compute scaling factor
        ax_pos = self.ax.get_position()
        scaling_factor = (ax_pos.y1 - ax_pos.y0) / (self.top - self.bottom)

        # Set font size for normal texts
        fontsize = self.fig.get_figheight() * scaling_factor * scale
        for tempo_text in self.tempo_texts:
            tempo_text.set_fontsize(fontsize)
            tempo_text.set_fontfamily("serif")

        # Set music font for tempo notes
        prop_small = FontProperties(fname=self.font_path, size=fontsize)
        for tempo_note in self.tempo_notes:
            tempo_note.set_fontproperties(prop_small)

        # Set music font for music texts
        prop = FontProperties(fname=self.font_path, size=fontsize * 2)
        for key_signature in self.key_signatures:
            key_signature.set_fontproperties(prop)
        for time_signature in self.time_signatures:
            time_signature.set_fontproperties(prop)
        for clef in self.clefs:
            clef.set_fontproperties(prop)
        for note in self.notes:
            note.set_fontproperties(prop)

    def update_boundaries(
        self,
        left: float = None,
        right: float = None,
        bottom: float = None,
        top: float = None,
    ):
        """Update boundaries."""
        if left is not None:
            self.left = min(self.left, left)
        if right is not None:
            self.right = max(self.right, right)
        if bottom is not None:
            self.bottom = min(self.bottom, bottom)
        if top is not None:
            self.top = max(self.top, top)

    def plot_staffs(
        self, start: float = None, end: float = None
    ) -> List[Line2D]:
        """Plot the staffs."""
        if start is None:
            start = 0
        if end is None:
            end = self._pos

        staffs = []
        for y in range(5):
            staff = Line2D(
                [start, end],
                [self._baseline + y, self._baseline + y],
                color="k",
                linewidth=2,
            )
            self.ax.add_line(staff)
            staffs.append(staff)

        # Update boundaries
        self.update_boundaries(
            left=start - 1,
            right=end + 1,
            bottom=self._baseline - 1,
            top=self._baseline + 5,
        )
        return staffs

    def plot_bar_line(self) -> Line2D:
        """Plot a bar line."""
        bar_line = Line2D(
            (self._pos, self._pos),
            (self._baseline, self._baseline + 4),
            linewidth=2,
            color="k",
        )
        self.ax.add_line(bar_line)
        # Update boundaries
        self.update_boundaries(left=self._pos - 1, right=self._pos + 1)
        # Move position cursor
        self._pos += 1
        # Force the next note to be a new note
        self._force_new_note = True
        return bar_line

    def plot_final_bar_line(self) -> List[Artist]:
        """Plot an ending bar line."""
        bar_line = Line2D(
            (self._pos, self._pos),
            (self._baseline, self._baseline + 4),
            linewidth=2,
            color="k",
        )
        self.ax.add_line(bar_line)
        thick_bar_line = Rectangle(
            (self._pos + 0.5, self._baseline), 0.5, 4, color="k", linewidth=2,
        )
        self.ax.add_patch(thick_bar_line)
        # Update boundaries
        self.update_boundaries(left=self._pos - 1, right=self._pos + 1)
        # Move position cursor
        self._pos += 1
        return [bar_line, thick_bar_line]

    def plot_clef(self, kind="treble", octave=0) -> Text:
        """Plot a clef."""
        # Treble clef
        if kind.lower() == "treble":
            if octave == 0:
                clef = self.ax.text(self._pos, 1, "\uE050")
                self._clef_offset = 0
            elif octave == 1:
                clef = self.ax.text(self._pos, 1, "\uE053")
                self._clef_offset = -3.5
            elif octave == -1:
                clef = self.ax.text(self._pos, 1, "\uE052")
                self._clef_offset = 3.5
            elif octave == 2:
                clef = self.ax.text(self._pos, 1, "\uE054")
                self._clef_offset = -7
            elif octave == -2:
                clef = self.ax.text(self._pos, 1, "\uE051")
                self._clef_offset = 7
            else:
                raise ValueError(
                    "`octave` must be one of 0, ±1, ±2 for a treble clef."
                )
            # Update boundaries
            self.update_boundaries(
                bottom=self._baseline - 2, top=self._baseline + 6
            )

        # Alto clef
        elif kind.lower() == "alto":
            if octave == 0:
                clef = self.ax.text(self._pos, 2, "\uE05C")
                self._clef_offset = 3
            elif octave == -1:
                clef = self.ax.text(self._pos, 2, "\uE05D")
                self._clef_offset = 6.5
            else:
                raise ValueError(
                    "`octave` must be either 0 or -1 for an alto clef."
                )
            # Update boundaries
            self.update_boundaries(bottom=self._baseline - 1)

        # Bass clef
        elif kind.lower() == "bass":
            if octave == 0:
                clef = self.ax.text(self._pos, 3, "\uE062")
                self._clef_offset = 6
            elif octave == 1:
                clef = self.ax.text(self._pos, 3, "\uE065")
                self._clef_offset = 2.5
            elif octave == -1:
                clef = self.ax.text(self._pos, 3, "\uE064")
                self._clef_offset = 9.5
            elif octave == 2:
                clef = self.ax.text(self._pos, 3, "\uE066")
                self._clef_offset = -1
            elif octave == -2:
                clef = self.ax.text(self._pos, 3, "\uE063")
                self._clef_offset = 13
            else:
                raise ValueError(
                    "`octave` must be one of 0, ±1, ±2 for a bass clef."
                )
            # Update boundaries
            self.update_boundaries(bottom=self._baseline - 1)

        # Append clef to the correpsonding attribute
        self.clefs.append(clef)
        # Update boundaries
        self.update_boundaries(left=self._pos - 1, right=self._pos + 4)
        # Move position cursor
        self._pos += 4
        # Force the next note to be a new note
        self._force_new_note = True
        return clef

    def plot_tempo(self, qpm) -> List[Artist]:
        """Plot a tempo as a metronome mark."""
        note = self.ax.text(self._pos, 7, "\uE1D5", ha="right")
        self.tempo_notes.append(note)
        text = self.ax.text(self._pos, 7, " = " + str(int(qpm)))
        self.tempo_texts.append(text)
        # Update boundaries
        self.update_boundaries(
            left=self._pos - 2, right=self._pos + 4, top=self._baseline + 10
        )
        return [note, text]

    def plot_key_signature(self, root: int, mode: str):
        """Plot a key signature. Supports only major and minor keys."""
        # self._accidentals = _get_accidentals(0)
        # self._pitches = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
        # TODO: Support keys other than major and minor keys

    def plot_time_signature(
        self, numerator: int, denominator: int
    ) -> List[Text]:
        """Plot a time signature."""
        numerator_text = self.ax.text(
            self._pos + 1, 3, get_time_signature_code(numerator), ha="center"
        )
        self.time_signatures.append(numerator_text)
        denominator_text = self.ax.text(
            self._pos + 1, 1, get_time_signature_code(denominator), ha="center"
        )
        self.time_signatures.append(denominator_text)
        # Update boundaries
        self.update_boundaries(
            left=self._pos - 1,
            right=self._pos + 5,
            bottom=self._baseline - 2,
            top=self._baseline + 6,
        )
        # Move position cursor
        self._pos += 4
        # Force the next note to be a new note
        self._force_new_note = True
        return [numerator_text, denominator_text]

    def plot_note(
        self, time, duration, pitch
    ) -> Optional[Tuple[List[Text], List[Arc]]]:
        """Plot a note."""
        if time < self._last_note_time:
            warnings.warn(
                "Note times must be sorted. Skipped unsorted one.",
                RuntimeWarning,
            )
            return None

        # If force new note is set, reset all state variables
        if self._force_new_note:
            self._last_note_pos = self._pos
            self._splits_max = 0
            self._bottom_note_y = self._baseline
            self._top_note_y = self._baseline + 4

        # If not a chord, reset all state variables
        elif time > self._last_note_time:
            self._pos = (
                self._last_note_pos + self.note_spacing * self._splits_max
            )
            self._last_note_pos = self._pos
            self._splits_max = 0
            self._bottom_note_y = self._baseline
            self._top_note_y = self._baseline + 4

        # If not a chord, set position back to last note
        else:
            self._pos = self._last_note_pos

        # Compute note position
        octave, pitch_class = divmod(pitch, 12)
        note_y = (
            self._pitch_classes[pitch_class] / 2
            + (octave - 5) * 3.5
            - 1
            + self._clef_offset
        )

        # Get note codes
        if (
            not self._force_new_note
            and time == self._last_note_time
            and note_y + 3.5 > self._last_note_y
        ):
            note_codes = to_note_codes_alt(duration * 0.25 / self.resolution)
        else:
            note_codes = to_note_codes(duration * 0.25 / self.resolution)

        # Plot notes
        texts: List[Text] = []
        ties: List[Arc] = []
        for i, code in enumerate(note_codes):
            # Note without an accidental
            if self._accidentals[pitch_class] is None:
                text = self.ax.text(self._pos, note_y, code)
            # Note with a sharp
            elif self._accidentals[pitch_class] == 1:
                text = self.ax.text(self._pos - 1, note_y, "\uE262" + code)
            # Note with a flat
            elif self._accidentals[pitch_class] == -1:
                text = self.ax.text(self._pos - 1, note_y, "\uE260" + code)
            # Note with a natural
            elif self._accidentals[pitch_class] == 0:
                text = self.ax.text(self._pos - 1, note_y, "\uE261" + code)
            self.notes.append(text)
            texts.append(text)

            # Plot a slur if not the first note
            if i > 0:
                x_center = self._pos - self.note_spacing * 0.5 + 0.7
                # Upper half
                tie = Arc(
                    (x_center, note_y + 1.8),
                    1.4 * self.note_spacing,
                    1.4 * self.note_spacing,
                    theta1=240,
                    theta2=300,
                    linewidth=2,
                )
                self.ax.add_patch(tie)
                self.ties.append(tie)
            self._pos += self.note_spacing

        # Extend margins
        self._splits_max = max(self._splits_max, len(note_codes))
        self._last_note_time = time
        self._last_note_y = note_y

        # Plot ledger lines
        if note_y < self._bottom_note_y:
            for y in range(int(note_y), int(self._bottom_note_y)):
                self.ax.plot(
                    (
                        self._pos - self.note_spacing - 0.4,
                        self._pos - self.note_spacing + 1.7,
                    ),
                    (y, y),
                    linewidth=2,
                    color="k",
                )
            self._bottom_note_y = note_y

        elif note_y > self._top_note_y:
            for y in range(int(self._top_note_y) + 1, int(note_y) + 1):
                self.ax.plot(
                    (
                        self._pos - self.note_spacing - 0.4,
                        self._pos - self.note_spacing + 1.7,
                    ),
                    (y, y),
                    linewidth=2,
                    color="k",
                )
            self._top_note_y = note_y

        # Update boundaries
        self.update_boundaries(
            left=self._pos + self.note_spacing,
            right=self._last_note_pos - 1,
            bottom=self._baseline + note_y - 2.5,
            top=self._baseline + note_y + 5.5,
        )

        self._force_new_note = False

        return texts, ties

    def plot_object(self, obj):
        """Plot an object."""
        if isinstance(obj, Note):
            self.plot_note(obj.time, obj.duration, obj.pitch)
        elif isinstance(obj, Tempo):
            self.plot_tempo(obj.qpm)
        elif isinstance(obj, TimeSignature):
            self.plot_time_signature(obj.numerator, obj.denominator)
        elif isinstance(obj, KeySignature):
            self.plot_key_signature(obj.root, obj.mode)


def show_score(
    music: "Music",
    figsize: Tuple[float, float] = None,
    clef: str = "treble",
    clef_octave: int = 0,
    note_spacing: int = None,
    font_path: Union[str, Path] = None,
    font_scale: float = None,
) -> ScorePlotter:
    """Show score visualization.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to show.
    figsize : (float, float), optional
        Width and height in inches. Defaults to Matplotlib
        configuration.
    clef : {'treble', 'alto', 'bass'}, default: 'treble'
        Clef type.
    clef_octave : int, default: 0
        Clef octave.
    note_spacing : int, default: 4
        Spacing of notes.
    font_path : str or Path, optional
        Path to the music font. Defaults to the path to the downloaded
        Bravura font.
    font_scale : float, default: 140
        Font scaling factor for finetuning. The default value of 140 is
        optimized for the default Bravura font.

    Returns
    -------
    :class:`muspy.ScorePlotter`
        A ScorePlotter object that handles the score.

    """
    # Create a figure
    fig = plt.figure(figsize=figsize)

    # Add a full-size axes (will be resized at the end)
    ax = fig.add_axes((0, 0, 1, 1))

    # Create a score plotter
    plotter = ScorePlotter(
        fig,
        ax,
        resolution=music.resolution,
        note_spacing=note_spacing,
        font_path=font_path,
        font_scale=font_scale,
    )

    # Begining bar line
    plotter.plot_bar_line()

    # Clef
    plotter.plot_clef(kind=clef, octave=clef_octave)

    # Tempos, key signatures, time signatures and notes
    notes = []
    for track in music.tracks:
        notes += track.notes
    notes.sort(key=lambda x: (x.time, -x.pitch, x.duration))

    objects: List[Base] = []
    objects += music.key_signatures
    objects += music.time_signatures
    objects += music.tempos
    objects += notes
    objects.sort(key=attrgetter("time"))
    for obj in objects:
        plotter.plot_object(obj)

    # Final bar line
    plotter.plot_final_bar_line()

    # Staff lines
    plotter.plot_staffs()

    # Adjust fonts
    plotter.adjust_fonts(scale=font_scale)

    return plotter
