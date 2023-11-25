"""ABC output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Union, List

from music21.pitch import Pitch

if TYPE_CHECKING:
    from ..music import Music


def generate_header(
    music: "Music"
) -> List[str]:
    """Generate ABC header from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC header.
    """
    header_lines = ["X: 1"]

    # TODO: set filename as title if no other title
    header_lines.append(f"T: {music.metadata.title}")
    creators = music.metadata.creators
    if (creators):
        header_lines.append(f"C: {','.join(creators)}")
    numerator = music.time_signatures[0].numerator
    denominator = music.time_signatures[0].denominator

    # TODO:  4/4 should be C and 2/2 should be C|
    header_lines.append(f"M: {numerator}/{denominator}")
    header_lines.append(f"L: 1/{denominator}")
    note = Pitch(music.key_signatures[0].root)
    mode = music.key_signatures[0].mode if music.key_signatures[0].mode is not None else ''
    header_lines.append(f"K: {note.name + mode}")
    return header_lines


def note_to_abc_str(
    note: Pitch
) -> str:
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


def note_lenght_to_str(
        note_lenght: float
) -> str:
    """Convert note lenght to string.

    Parameters
    ----------
    note_lenght : float, default: False
        note length relative to the default note length
    """
    numerator, denominator = note_lenght.as_integer_ratio()
    note_lenght_str = ''
    if numerator != 1:
        note_lenght_str += str(numerator)
    if denominator != 1:
        note_lenght_str += '/' + str(denominator)
    return note_lenght_str


def get_note_lenght(
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
    note_lenght_in_dflt_lenght = note_length_in_quarters * dflt_lenght_in_quarters
    note_lenght_str = note_lenght_to_str(note_lenght_in_dflt_lenght)
    return note_lenght_str


def generate_note_body(
    music: "Music"
) -> str:
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    resolution = music.resolution
    dflt_len_in_quarters = music.time_signatures[0].denominator / 4
    barlines = music.barlines
    bar_iter = 0
    notes = music.tracks[0].notes
    note_iter = 0
    note_str = ''
    # TODO generate notes in several lines instead of 1
    while bar_iter < len(barlines) and note_iter < len(notes):
        if barlines[bar_iter].time <= notes[note_iter].time:
            note_str += ' | '
            bar_iter += 1
        else:
            note_str += note_to_abc_str(Pitch(midi=notes[note_iter].pitch))
            note_str += get_note_lenght(notes[note_iter],
                                        resolution, dflt_len_in_quarters)
            note_iter += 1
    while note_iter < len(notes):
        note_str += note_to_abc_str(Pitch(midi=notes[note_iter].pitch))
        note_str += get_note_lenght(notes[note_iter],
                                    resolution, dflt_len_in_quarters)
        note_iter += 1
    note_str += ' |'
    return note_str.lstrip()


def write_abc(
    path: Union[str, Path], music: "Music"
):
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
    with open(path, 'w') as file:
        for line in file_lines:
            file.write(f"{line}\n")
