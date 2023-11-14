"""ABC output interface."""
from pathlib import Path
from typing import Union

from music21.pitch import Pitch
from ..music import Music


def generate_header(
    music: Music
) -> list[str]:
    """Generate ABC header from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC header.
    """
    header_lines = ["X:1"]

    # TODO: set filename as title if no other title
    header_lines.append(f"T:{music.metadata.title}")
    if (creators := music.metadata.creators):
        header_lines.append(f"C:{','.join(creators)}")
    numerator = music.time_signatures[0].numerator
    denominator = music.time_signatures[0].denominator

    # TODO:  4/4 should be C and 2/2 should be C|
    header_lines.append(f"M:{numerator}/{denominator}")
    header_lines.append(f"L:1/{denominator}")
    note = Pitch(music.key_signatures[0].root)
    mode = music.key_signatures[0].mode if music.key_signatures[0].mode is not None else ''
    header_lines.append(f"K:{note.name+mode}")
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


def generate_note_body(
    music: Music
) -> str:
    """Generate ABC note body from Music object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to generate ABC note body.
    """
    barlines = music.barlines
    bar_iter = 0
    notes = music.tracks[0].notes
    note_iter = 0
    note_str = ''
    while bar_iter < len(barlines) and note_iter < len(notes):
        if barlines[bar_iter].time <= notes[note_iter].time:
            note_str += ' | '
            bar_iter += 1
        else:
            note_str += note_to_abc_str(Pitch(midi=notes[note_iter].pitch))
            note_iter += 1
    while note_iter < len(notes):
        note_str += note_to_abc_str(Pitch(midi=notes[note_iter].pitch))
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
