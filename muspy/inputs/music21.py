"""Music21 input interface."""
from typing import Dict, List, Tuple, Union

from music21.instrument import partitionByInstrument
from music21.stream import Opus, Part, Score, Stream

from ..classes import (
    Chord,
    KeySignature,
    Metadata,
    Note,
    Tempo,
    TimeSignature,
    Track,
)
from ..music import DEFAULT_RESOLUTION, Music


def parse_metadata(stream: Stream) -> Union[Metadata, None]:
    """Return metadata parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to parse.

    Returns
    -------
    :class:`muspy.Metadata` object
        Parsed metadata.

    """
    if stream.metadata is None:
        return None

    creators = []
    for contributor in stream.metadata.contributors:
        creators.extend(contributor.names)

    copyright_ = None
    for item in stream.metadata.all(skipContributors=True):
        if item[0] == "copyright":
            copyright_ = item[1]

    return Metadata(
        title=stream.metadata.title, creators=creators, copyright=copyright_,
    )


def parse_tempos(stream: Stream, resolution=DEFAULT_RESOLUTION) -> List[Tempo]:
    """Return tempos parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Tempo` objects
        Parsed tempos.

    """
    tempos = []
    for start, _, metronome in stream.flat.metronomeMarkBoundaries():
        time = int(float(start * resolution))
        tempo = Tempo(time, metronome.getQuarterBPM())
        tempos.append(tempo)
    return tempos


def parse_key_signatures(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> List[KeySignature]:
    """Return key signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.KeySignature` objects
        Parsed key signatures.

    """
    key_signatures = []
    for item in stream.flat.getKeySignatures():
        time = int(float(item.offset * resolution))
        key_signature = KeySignature(time, item.tonic.pitchClass, item.mode)
        key_signatures.append(key_signature)
    return key_signatures


def parse_time_signatures(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> List[TimeSignature]:
    """Return time signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.TimeSignature` objects
        Parsed time signatures.

    """
    time_signatures = []
    for item in stream.flat.getTimeSignatures():
        time = int(float(item.offset * resolution))
        time_signature = TimeSignature(time, item.numerator, item.denominator)
        time_signatures.append(time_signature)
    return time_signatures


def parse_notes_and_chords(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> Tuple[List[Note], List[Chord]]:
    """Return notes and chords parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Note` objects
        Parsed notes.
    list of :class:`muspy.Chord` objects
        Parsed chords.

    """
    notes: List[Note] = []
    chords: List[Chord] = []
    ties: Dict[int, int] = {}

    for item in stream.flat.notesAndRests:
        # Ignore rests
        if not item.isNote and not item.isChord:
            continue

        # Ignore grace notes
        if item.duration.isGrace:
            continue

        # Parse note
        time = int(round(float(item.offset * resolution)))
        duration = int(round(float(item.quarterLength) * resolution))

        if item.isNote:
            pitch = int(item.pitch.midi)
            is_outgoing_tie = item.tie and (
                item.tie.type == "start" or item.tie.type == "continue"
            )
            if pitch in ties:
                note_idx = ties[pitch]
                notes[note_idx].duration += duration
                if is_outgoing_tie:
                    ties[pitch] = note_idx
                else:
                    del ties[pitch]
            else:
                note = Note(time, duration, int(item.pitch.midi),)
                notes.append(note)
                if is_outgoing_tie:
                    ties[pitch] = len(notes) - 1

        elif item.isChord:
            pitches = [note.pitch.midi for note in item.notes]
            chord = Chord(time, duration, pitches)
            chords.append(chord)

    return notes, chords


def parse_track(part: Part, resolution=DEFAULT_RESOLUTION) -> Track:
    """Return track parsed from a music21 Part object.

    Parameters
    ----------
    part : `music21.stream.Part` object
        Part object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Track` object
        Parsed track.

    """
    notes, chords = parse_notes_and_chords(part, resolution)

    instrument = part.getInstrument()

    if instrument.midiProgram is not None:
        program = instrument.midiProgram
    else:
        program = 0

    if instrument.midiChannel is not None:
        is_drum = instrument.midiChannel == 10
    else:
        is_drum = False

    return Track(
        program=program,
        is_drum=is_drum,
        name=part.partName,
        notes=notes,
        chords=chords,
    )


def from_music21_part(
    part: Part, resolution=DEFAULT_RESOLUTION
) -> Union[Track, List[Track]]:
    """Return track(s) parsed from a music21 Part object.

    Parameters
    ----------
    part : `music21.stream.Part` object
        Part object to parse.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Track` object or list of :class:`muspy.Track` object
        Parsed track(s).

    """
    instruments = partitionByInstrument(part)
    if len(instruments) > 1:
        return [
            parse_track(instrument, resolution) for instrument in instruments
        ]
    return parse_track(part, resolution)


def from_music21_opus(
    opus: Opus, resolution=DEFAULT_RESOLUTION
) -> List[Music]:
    """Return a list of Music objects converted from a music21 Opus object.

    Parameters
    ----------
    opus : `music21.stream.Opus` object
        Opus object to convert.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    return [from_music21_score(score, resolution) for score in opus.scores]


def from_music21_score(score: Score, resolution=DEFAULT_RESOLUTION) -> Music:
    """Return a Music object converted from a music21 Stream object.

    Parameters
    ----------
    score : `music21.stream.Score` object
        Score object to convert.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted Music object.

    """
    tracks = []
    for part in score.parts:
        instruments = partitionByInstrument(part)
        if instruments:
            for instrument in instruments:
                tracks.append(parse_track(instrument))
        elif len(part.flat.notesAndRests) > 0:
            tracks.append(parse_track(part))

    return Music(
        metadata=parse_metadata(score),
        resolution=DEFAULT_RESOLUTION,
        tempos=parse_tempos(score),
        key_signatures=parse_key_signatures(score, resolution),
        time_signatures=parse_time_signatures(score, resolution),
        tracks=tracks,
    )


def from_music21(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> Union[Music, List[Music], Track, List[Track]]:
    """Return a Music object converted from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to convert.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object(s) or :class:`muspy.Track` object(s)
        Converted Music object(s) or Track object(s).

    """
    if isinstance(stream, Opus):
        return from_music21_opus(stream, resolution)
    elif isinstance(stream, Part):
        return from_music21_part(stream, resolution)
    else:
        return from_music21_score(stream, resolution)

    tracks = []
    if isinstance(stream, Score):
        for part in stream.parts:
            instruments = partitionByInstrument(part)
            if instruments:
                for instrument in instruments:
                    tracks.append(parse_track(instrument))
            elif len(part.flat.notesAndRests) > 0:
                tracks.append(parse_track(part))
    else:
        instruments = partitionByInstrument(stream)
        if instruments:
            for instrument in instruments:
                tracks.append(parse_track(instrument))
        elif len(stream.flat.notesAndRests) > 0:
            tracks.append(parse_track(stream))

    return Music(
        metadata=parse_metadata(stream),
        resolution=DEFAULT_RESOLUTION,
        tempos=parse_tempos(stream),
        key_signatures=parse_key_signatures(stream, resolution),
        time_signatures=parse_time_signatures(stream, resolution),
        tracks=tracks,
    )
