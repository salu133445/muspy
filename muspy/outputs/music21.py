"""Music21 converter interface."""
from typing import TYPE_CHECKING, Any

from music21.metadata import Copyright, Contributor, Metadata
from music21.note import Note
from music21.stream import Part, Score, Stream

if TYPE_CHECKING:
    from ..music import Music

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _get_pitch_name(note_number: int) -> str:
    octave, pitch_class = divmod(note_number, 12)
    return PITCH_NAMES[pitch_class] + str(octave - 1)


def to_music21(music: "Music", **kwargs: Any) -> Stream:
    """Write a Music object to a music21 stream object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    stream : `music21.stream.Stream` object
        Converted music21 stream object.

    """
    # Create a new part
    score = Score()

    # === Metadata ===
    if music.metadata:
        # Create a new metadata
        metadata = Metadata()

        # Set title
        if music.metadata.title:
            metadata.title = music.metadata.title

        # Set copyright
        if music.metadata.copyright:
            metadata.copyright = Copyright(music.metadata.copyright)

        # Add contributors
        for creator in music.metadata.creators:
            metadata.addContributor(Contributor(name=creator))

    # Append metadata to score
    score.append(metadata)

    # === Tracks ===
    for track in music.tracks:
        # Create a new part
        part = Part()

        # Add notes to part
        for note in track.notes:
            m21_note = Note(_get_pitch_name(note.pitch))
            m21_note.quarterLength = note.duration / music.resolution
            part.append(m21_note)

        # Append the part to score
        score.append(part)

    return score
