"""Music21 input interface."""
from typing import List, Tuple, Union

from music21.instrument import partitionByInstrument
from music21.stream import Opus, Score, Stream

from ..classes import (
    Chord,
    KeySignature,
    MetaData,
    Note,
    SongInfo,
    SourceInfo,
    Tempo,
    TimeSignature,
    Track,
)
from ..music import DEFAULT_RESOLUTION, Music


def parse_notes_and_chords(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> Tuple[List[Note], List[Chord]]:
    """Return notes and chords parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Note` objects
        Parsed notes.
    list of :class:`muspy.Chord` objects
        Parsed chords.

    """
    notes = []
    chords = []
    for item in stream.flat.notesAndRests:
        if not item.isNote and not item.isChord:
            continue
        start = int(float(item.offset * resolution))
        duration = int(float(item.duration.quarterLength) * resolution)
        if item.isNote:
            note = Note(
                start=start, end=start + duration, pitch=int(item.pitch.midi)
            )
            notes.append(note)
        elif item.isChord:
            pitches = [note.pitch.midi for note in item.notes]
            chord = Chord(start=start, end=start + duration, pitches=pitches)
            chords.append(chord)
    return notes, chords


def parse_track(stream: Stream, resolution=DEFAULT_RESOLUTION) -> Track:
    """Return track parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Track` object
        Parsed track.

    """
    instrument = stream.getInstrument()
    notes, chords = parse_notes_and_chords(stream, resolution)
    return Track(
        program=instrument.midiProgram,
        is_drum=(instrument.midiChannel == 10),
        notes=notes,
        chords=chords,
    )


def parse_key_signatures(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> List[KeySignature]:
    """Return key signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.KeySignature` objects
        Parsed key signatures.

    """
    key_signatures = []
    for item in stream.getKeySignatures():
        time = int(float(item.offset * resolution))
        key_signature = KeySignature(
            time, str(item.tonic).replace("-", "b"), str(item.mode)
        )
        key_signatures.append(key_signature)
    return key_signatures


def parse_time_signatures(
    stream: Stream, resolution=DEFAULT_RESOLUTION
) -> List[TimeSignature]:
    """Return time signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.TimeSignature` objects
        Parsed time signatures.

    """
    time_signatures = []
    for item in stream.getTimeSignatures():
        time = int(float(item.offset * resolution))
        time_signature = TimeSignature(
            time, int(item.numerator), int(item.denominator)
        )
        time_signatures.append(time_signature)
    return time_signatures


def parse_meta_data(stream: Stream) -> Union[MetaData, None]:
    """Return meta data parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.

    Returns
    -------
    :class:`muspy.MetaData` object
        Parsed meta data.

    """
    if stream.metadata is None:
        return None

    creators = []
    for contributor in stream.metadata.contributors:
        creators.extend(contributor.names)

    copyright_ = None
    for item in stream.metadata.all(True):
        if item[0] == "copyright":
            copyright_ = item[1]

    return MetaData(
        song=SongInfo(
            title=stream.metadata.title, artist=stream.metadata.composer,
        ),
        source=SourceInfo(copyright=copyright_),
    )


def parse_tempos(stream: Stream, resolution=DEFAULT_RESOLUTION) -> List[Tempo]:
    """Return tempos parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream` object
        Stream object to be parsed.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    list of :class:`muspy.Tempo` objects
        Parsed tempos.

    """
    tempos = []
    for start, _, metronome in stream.metronomeMarkBoundaries():
        time = int(float(start * resolution))
        tempo = Tempo(time, metronome.getQuarterBPM())
        tempos.append(tempo)
    return tempos


def from_music21_opus(
    opus: Opus, resolution=DEFAULT_RESOLUTION
) -> List[Music]:
    """Return a list of Music objects converted from a music21 Opus object.

    Parameters
    ----------
    opus : `music21.stream.Opus`
        Stream object to be converted.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    return [from_music21(score, resolution) for score in opus.scores]


def from_music21(stream: Stream, resolution=DEFAULT_RESOLUTION) -> Music:
    """Return a Music object converted from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to be converted.
    resolution : int, optional
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.

    Returns
    -------
    :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    if isinstance(stream, Opus):
        raise TypeError(
            "Please use `from_music21_opus` for a music21 Opus object."
        )

    tracks = []
    if isinstance(stream, Score):
        for part in stream.parts:
            instruments = partitionByInstrument(part)
            if instruments:
                for instrument in instruments:
                    tracks.append(parse_track(instrument))
            else:
                tracks.append(parse_track(part))
    else:
        instruments = partitionByInstrument(stream)
        if instruments:
            for instrument in instruments:
                tracks.append(parse_track(instrument))
        else:
            tracks.append(parse_track(stream))

    return Music(
        resolution=DEFAULT_RESOLUTION,
        tempos=parse_tempos(stream),
        key_signatures=parse_key_signatures(stream, resolution),
        time_signatures=parse_time_signatures(stream, resolution),
        tracks=tracks,
        meta=parse_meta_data(stream),
    )
