"""Music21 converter interface."""
from typing import TYPE_CHECKING

from music21.key import Key
from music21.metadata import Contributor, Copyright
from music21.metadata import Metadata as M21MetaData
from music21.meter import TimeSignature as M21TimeSignature
from music21.note import Note as M21Note
from music21.stream import Part, Score
from music21.tempo import MetronomeMark

from ..classes import KeySignature, Metadata, Tempo, TimeSignature
from ..utils import CIRCLE_OF_FIFTHS, MODE_CENTERS

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


def to_music21_key(key_signature: KeySignature) -> Key:
    """Return a KeySignature object as a music21 Key object."""
    if key_signature.root_str is not None:
        tonic = key_signature.root_str
    elif key_signature.root is not None:
        tonic = PITCH_NAMES[key_signature.root]
    elif key_signature.fifths is not None:
        if key_signature.mode is not None:
            offset = MODE_CENTERS[key_signature.mode]
            tonic = CIRCLE_OF_FIFTHS[key_signature.fifths + offset][1]
        else:
            tonic = CIRCLE_OF_FIFTHS[key_signature.fifths][1]
    else:
        raise ValueError(
            "One of `root`, `root_str` or `fifths` must be specified."
        )
    key = Key(tonic=tonic, mode=key_signature.mode)
    key.offset = key_signature.time
    return key


def to_music21_time_signature(
    time_signature: TimeSignature,
) -> M21TimeSignature:
    """Return a TimeSignature object as a music21 TimeSignature."""
    m21_time_signature = M21TimeSignature(
        f"{time_signature.numerator}/{time_signature.denominator}"
    )
    m21_time_signature.offset = time_signature.time
    return m21_time_signature


def to_music21_metadata(metadata: Metadata) -> M21MetaData:
    """Return a Metadata object as a music21 Metadata object.

    Parameters
    ----------
    metadata : :class:`muspy.Metadata`
        Metadata object to convert.

    Returns
    -------
    `music21.metadata.Metadata`
        Converted music21 Metadata object.

    """
    meta = M21MetaData()

    # Title is usually stored in movement-title. See
    # https://www.musicxml.com/tutorial/file-structure/score-header-entity/
    if metadata.title:
        meta.movementName = metadata.title

    if metadata.copyright:
        meta.copyright = Copyright(metadata.copyright)
    for creator in metadata.creators:
        meta.addContributor(Contributor(name=creator))
    return meta


def to_music21(music: "Music") -> Score:
    """Return a Music object as a music21 Score object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to convert.

    Returns
    -------
    `music21.stream.Score`
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
        part.partName = track.name

        # Add tempos
        for tempo in music.tempos:
            part.append(to_music21_metronome(tempo))

        # Add time signatures
        for time_signature in music.time_signatures:
            part.append(to_music21_time_signature(time_signature))

        # Add key signatures
        for key_signature in music.key_signatures:
            part.append(to_music21_key(key_signature))

        # Add notes to part
        for note in track.notes:
            m21_note = M21Note(_get_pitch_name(note.pitch))
            m21_note.quarterLength = note.duration / music.resolution
            offset = note.time / music.resolution
            part.insert(offset, m21_note)

        # Append the part to score
        score.append(part)

    return score
