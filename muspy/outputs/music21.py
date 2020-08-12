"""Music21 converter interface."""
from typing import TYPE_CHECKING

from music21.metadata import Copyright, Contributor
from music21.metadata import Metadata as M21MetaData
from music21.note import Note as M21Note
from music21.stream import Part, Score
from music21.tempo import MetronomeMark

from ..classes import Metadata, Tempo

if TYPE_CHECKING:
    from ..music import Music

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _get_pitch_name(note_number: int) -> str:
    octave, pitch_class = divmod(note_number, 12)
    return PITCH_NAMES[pitch_class] + str(octave - 1)


def to_music21_metronome(tempo: Tempo) -> MetronomeMark:
    """Return a Tempo object as a music21 MetronomeMark object."""
    metronome = MetronomeMark(number=tempo.qpm)
    metronome.offset = tempo.time
    return metronome


def to_music21_metadata(metadata: Metadata) -> M21MetaData:
    """Convert a Metadata object to a music21 Metadata object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    `music21.metadata.Metadata` object
        Converted music21 Score object.

    """
    meta = M21MetaData()

    # Title is usually stored in movement-title
    # See https://www.musicxml.com/tutorial/file-structure/score-header-entity/
    if metadata.title:
        meta.movementName = metadata.title

    if metadata.copyright:
        meta.copyright = Copyright(metadata.copyright)
    for creator in metadata.creators:
        meta.addContributor(Contributor(name=creator))
    return meta


def to_music21(music: "Music") -> Score:
    """Convert a Music object to a music21 Score object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        MusPy Music object to be converted.

    Returns
    -------
    `music21.stream.Score` object
        Converted music21 Score object.

    """
    # Create a new score
    score = Score()

    # Metadata
    if music.metadata:
        score.append(to_music21_metadata(music.metadata))

    # Tracks
    for track in music.tracks:
        # Create a new part
        part = Part()

        # Add notes to part
        for note in track.notes:
            m21_note = M21Note(_get_pitch_name(note.pitch))
            m21_note.offset = note.time / music.resolution
            m21_note.quarterLength = note.duration / music.resolution
            part.append(m21_note)

        # Append the part to score
        score.append(part)

    return score
