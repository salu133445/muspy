"""Music21 input interface."""
from operator import attrgetter
from typing import Dict, List, Tuple, Union

import numpy as np
from music21.instrument import partitionByInstrument
from music21.key import Key
from music21.key import KeySignature as M21KeySignature
from music21.stream import Opus, Part, Score, Stream

from ..classes import (
    Barline,
    Beat,
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
    stream : `music21.stream.Stream`
        Stream object to parse.

    Returns
    -------
    :class:`muspy.Metadata`
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
        title=stream.metadata.title,
        creators=creators,
        copyright=copyright_,
        source_format="music21",
    )


def parse_tempos(
    stream: Stream, resolution: int = DEFAULT_RESOLUTION
) -> List[Tempo]:
    """Return tempos parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.Tempo`
        Parsed tempos.

    """
    tempos = set()
    for start, _, metronome in stream.flat.metronomeMarkBoundaries():
        tempo = Tempo(
            time=round(float(start * resolution)),
            qpm=metronome.getQuarterBPM(),
        )
        tempos.add(tempo)
    return sorted(tempos, key=attrgetter("time"))


def parse_key_signatures(
    stream: Stream, resolution: int = DEFAULT_RESOLUTION
) -> List[KeySignature]:
    """Return key signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.KeySignature`
        Parsed key signatures.

    """
    key_signatures = set()
    for item in stream.flat.getElementsByClass(M21KeySignature):
        if isinstance(item, Key):
            key_signatures.add(
                KeySignature(
                    time=round(float(item.offset * resolution)),
                    root=item.tonic.pitchClass,
                    mode=item.mode,
                    fifths=item.sharps,
                )
            )
        else:
            key_signatures.add(
                KeySignature(
                    time=round(float(item.offset * resolution)),
                    fifths=item.sharps,
                )
            )
    return sorted(key_signatures, key=attrgetter("time"))


def parse_time_signatures(
    stream: Stream, resolution: int = DEFAULT_RESOLUTION
) -> List[TimeSignature]:
    """Return time signatures parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.TimeSignature`
        Parsed time signatures.

    """
    time_signatures = set()
    for item in stream.flat.getTimeSignatures():
        time_signature = TimeSignature(
            time=round(float(item.offset * resolution)),
            numerator=item.numerator,
            denominator=item.denominator,
        )
        time_signatures.add(time_signature)
    return sorted(time_signatures, key=attrgetter("time"))


def parse_barlines_and_beats(
    stream: Stream,
    time_signatures: List[TimeSignature],
    resolution: int = DEFAULT_RESOLUTION,
) -> Tuple[List[Barline], List[Beat]]:
    """Return barlines and beats parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to parse.
    time_signatures : list of :class:`muspy.TimeSignature`
        Time signature objects.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.Barline`
        Parsed barlines.
    list of :class:`muspy.Beat`
        Parsed beats.

    """
    # Initialize return lists
    barlines: List[Barline] = []
    beats: List[Beat] = []

    # Get barline positions
    measure_offset_map = stream.measureOffsetMap()
    for offset in measure_offset_map.keys():
        barlines.append(Barline(time=round(float(offset * resolution))))

    # Sort the barlines by time
    barlines.sort(key=attrgetter("time"))

    time_sign_idx = 0
    barline_idx = 0
    while barline_idx < len(barlines):
        # Use next time signature
        if (
            time_sign_idx < len(time_signatures) - 1
            and barlines[barline_idx].time
            >= time_signatures[time_sign_idx].time
        ):
            time_sign_idx += 1
            continue

        # Set time signature
        time_sign = time_signatures[time_sign_idx]
        beat_resolution = resolution / (time_sign.denominator / 4)

        # Get the next downbeat
        if barline_idx < len(barlines) - 1:
            end: float = barlines[barline_idx + 1].time
        else:
            end = (
                barlines[barline_idx].time
                + beat_resolution * time_sign.numerator
            )
        # Append beats
        for time in np.arange(
            barlines[barline_idx].time, end, beat_resolution
        ):
            beats.append(Beat(time=int(round(time))))
        barline_idx += 1

    return barlines, beats


def parse_notes_and_chords(
    stream: Stream, resolution: int = DEFAULT_RESOLUTION
) -> Tuple[List[Note], List[Chord]]:
    """Return notes and chords parsed from a music21 Stream object.

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    list of :class:`muspy.Note`
        Parsed notes.
    list of :class:`muspy.Chord`
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
        time = round(float(item.offset * resolution))
        duration = round(float(item.quarterLength) * resolution)
        velocity = item.volume.velocity
        if velocity is not None:
            velocity = round(velocity)

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
                note = Note(
                    time=time,
                    pitch=int(item.pitch.midi),
                    duration=duration,
                    velocity=velocity,
                )
                notes.append(note)
                if is_outgoing_tie:
                    ties[pitch] = len(notes) - 1

        elif item.isChord:
            chord = Chord(
                time=time,
                pitches=[int(note.pitch.midi) for note in item.notes],
                duration=duration,
                velocity=velocity,
            )
            chords.append(chord)

    return notes, chords


def parse_track(part: Part, resolution: int = DEFAULT_RESOLUTION) -> Track:
    """Return track parsed from a music21 Part object.

    Parameters
    ----------
    part : `music21.stream.Part`
        Part object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Track`
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
    part: Part, resolution: int = DEFAULT_RESOLUTION
) -> Union[Track, List[Track]]:
    """Return a music21 Part object as Track object(s).

    Parameters
    ----------
    part : `music21.stream.Part`
        Part object to parse.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Track` or list of :class:`muspy.Track`
        Parsed track(s).

    """
    instruments = partitionByInstrument(part)
    if not instruments:
        return parse_track(part, resolution)
    return [parse_track(instrument, resolution) for instrument in instruments]


def from_music21_score(
    score: Score, resolution: int = DEFAULT_RESOLUTION
) -> Music:
    """Return a music21 Stream object as a Music object.

    Parameters
    ----------
    score : `music21.stream.Score`
        Score object to convert.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    Warnings
    --------
    This function uses :method:`music21.Stream.expandRepeats` to
    expand the repeats. However, this does not always get the
    correct results. In particular, repeats with multiple endings are
    not yet supported in MusicXML parser of Music21.

    """
    if score.hasMeasures():
        score = score.expandRepeats()

    tracks = []
    for part in score.parts:
        if part.hasMeasures():
            part = part.expandRepeats()
        instruments = partitionByInstrument(part)
        if instruments:
            for instrument in instruments:
                tracks.append(parse_track(instrument))
        elif len(part.flat.notesAndRests) > 0:
            tracks.append(parse_track(part))

    meta_part = score.parts[0]
    if meta_part.hasMeasures():
        meta_part = meta_part.expandRepeats()
    key_signatures = parse_key_signatures(meta_part, resolution)
    time_signatures = parse_time_signatures(meta_part, resolution)
    barlines, beats = parse_barlines_and_beats(
        meta_part, time_signatures, resolution
    )

    return Music(
        metadata=parse_metadata(score),
        resolution=DEFAULT_RESOLUTION,
        tempos=parse_tempos(meta_part),
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        barlines=barlines,
        beats=beats,
        tracks=tracks,
    )


def from_music21_opus(
    opus: Opus, resolution: int = DEFAULT_RESOLUTION
) -> List[Music]:
    """Return a music21 Opus object as a list of Music objects.

    Parameters
    ----------
    opus : `music21.stream.Opus`
        Opus object to convert.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    """
    return [from_music21_score(score, resolution) for score in opus.scores]


def from_music21(
    stream: Stream, resolution: int = DEFAULT_RESOLUTION
) -> Union[Music, List[Music], Track, List[Track]]:
    """Return a music21 Stream object as Music or Track object(s).

    Parameters
    ----------
    stream : `music21.stream.Stream`
        Stream object to convert.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.

    Returns
    -------
    :class:`muspy.Music` or :class:`muspy.Track`
        Converted Music or Track object(s).

    """
    if isinstance(stream, Opus):
        return from_music21_opus(stream, resolution)
    elif isinstance(stream, Part):
        return from_music21_part(stream, resolution)
    else:
        return from_music21_score(stream, resolution)
