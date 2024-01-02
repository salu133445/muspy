"""ABC output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from music21.pitch import Pitch

if TYPE_CHECKING:
    from ..classes import Note
    from ..music import Barline, KeySignature, Music


class ObjectABC:
    def __init__(
        self,
        time=0,
        abc_str="",
        priority=0,
        pitch=None,
        duration=None,
        velocity=None,
    ) -> None:
        self.priority = priority
        self.time = time
        self.abc_str = abc_str

        # note
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity

    def __str__(self) -> str:
        return self.abc_str

    def __lt__(self, other):
        if self.time == other.time:
            return self.priority < other.priority
        return self.time < other.time

    def __gt__(self, other):
        if self.time == other.time:
            return self.priority > other.priority
        return self.time > other.time

    def __eq__(self, other):
        if self.is_note == other.is_note:
            return self.time == other.time
        return False


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


def note_to_abc_str(note: Pitch) -> str:
    """Generate string note in ABC style from Pitch object.

    Parameters
    ----------
    note : :class:`music21.pitch.Pitch`
        Pitch object to generate ABC note.
    """
    octave = note.octave
    if octave <= 4:
        comas = 4 - octave
        return note.name[0] + "," * comas
    else:
        apostrophes = octave - 5
        return note.name[0].lower() + "'" * apostrophes


def note_lenght_to_str(note_lenght: float) -> str:
    """Convert note lenght to string.

    Parameters
    ----------
    note_lenght : float, default: False
        note length relative to the default note length
    """
    numerator, denominator = note_lenght.as_integer_ratio()
    note_lenght_str = ""
    if numerator != 1:
        note_lenght_str += str(numerator)
    if denominator != 1:
        note_lenght_str += "/" + str(denominator)
    return note_lenght_str


def get_note_length(
    note: Pitch, resolution: int, dflt_lenght_in_quarters: float
) -> str:
    """Generate a note length indication from Music object.
    Use numeric symbols without '>', '<' signs.

    Parameters
    ----------
    note : :class:`music21.pitch.Pitch`
        Pitch object to generate ABC note.
    resolution: int
        Resolution
    dflt_lenght_in_quarters: float
        default note length relative to the quarters
    """
    note_length_in_quarters = note.duration / resolution
    note_lenght_in_dflt_lenght = (
        note_length_in_quarters * dflt_lenght_in_quarters
    )
    note_lenght_str = note_lenght_to_str(note_lenght_in_dflt_lenght)
    return note_lenght_str


def objectify_keys(keys: List["KeySignature"]) -> List[ObjectABC]:
    """Generate list of ABC keys.

    Parameters
    ----------
    keys : :class:`List[muspy.KeySignature]`
        List of muspy KeySignature objects.
    """
    abc_keys = []
    for key in keys:
        note = Pitch(key.root)
        mode = key.mode
        key_str = f"\nK:{note.name+mode}\n"
        abc_keys.append(ObjectABC(time=key.time, priority=2, abc_str=key_str))
    return abc_keys


def objectify_barlines(barlines: List["Barline"]) -> List[ObjectABC]:
    """Generate list of ABC barlines.

    Parameters
    ----------
    barlines : :class:`List[muspy.Barline]`
        List of muspy Barline objects.
    """
    if (
        barlines[0].time == 0
    ):  # The first barline is skipped. Assumption that barlines are sorted
        barlines = barlines[1:]
    abc_barlines = []
    for barline in barlines:
        abc_barlines.append(
            ObjectABC(time=barline.time, priority=1, abc_str=" | ")
        )
    return abc_barlines


def objectify_notes(
    notes: List["Note"], resolution, note_len
) -> List[ObjectABC]:
    """Generate list of ABC notes.

    Parameters
    ----------
    notes : :class:`List[muspy.Note]`
        List of muspy Note objects.
    """
    abc_notes = []
    for note in notes:
        new_note = ObjectABC(
            time=note.time,
            priority=3,
            pitch=Pitch(midi=note.pitch),
            duration=note.duration,
            velocity=note.velocity,
        )
        note_str = note_to_abc_str(new_note.pitch)
        note_str += get_note_length(new_note, resolution, note_len)
        new_note.abc_str = note_str
        abc_notes.append(new_note)
    return abc_notes


def generate_note_body(music: "Music") -> str:
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    abc_objects = []
    abc_objects += objectify_keys(music.key_signatures)
    abc_objects += objectify_barlines(music.barlines)

    resolution = music.resolution
    dflt_len_in_quarters = music.time_signatures[0].denominator / 4
    abc_objects += objectify_notes(
        music.tracks[0].notes,
        resolution=resolution,
        note_len=dflt_len_in_quarters,
    )
    abc_objects.sort()
    note_str = "".join(str(abc) for abc in abc_objects)
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

    path = str(path)
    if not path.endswith(".abc"):
        path += ".abc"

    file_lines = generate_header(music)
    file_lines.append(generate_note_body(music))

    # TODO: catch exceptions
    with open(path, "w") as file:
        for line in file_lines:
            file.write(f"{line}\n")
