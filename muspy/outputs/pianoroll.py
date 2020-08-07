"""Pianoroll output interface."""
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray
from pypianoroll import Multitrack, Track

from ..processor import PianoRollProcessor

if TYPE_CHECKING:
    from ..music import Music


def to_pypianoroll(music: "Music") -> Multitrack:
    """Return a Music object as a Multitrack object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    multitrack : :class:`pypianoroll.Multitrack` object
        Converted Multitrack object.

    """
    length = (music.get_end_time() // music.resolution + 1) * music.resolution

    # Tracks
    tracks = []
    for track in music.tracks:
        pianoroll = np.zeros((length, 128))
        for note in track.notes:
            pianoroll[
                note.time : note.end + 1, note.pitch  # type:ignore
            ] = note.velocity
        tracks.append(
            Track(
                pianoroll,
                track.program,
                track.is_drum,
                track.name if track.name is not None else "",
            )
        )

    # Tempos
    last_tempo_time = max((tempo.time for tempo in music.tempos))
    tempo_arr = 120.0 * np.ones(last_tempo_time + 1)
    qpm = 120.0
    position = 0
    for tempo in music.tempos:
        tempo_arr[position : tempo.time] = qpm  # type:ignore
        tempo_arr[tempo.time] = tempo.tempo  # type:ignore
        position = tempo.time + 1  # type:ignore
        qpm = tempo.tempo

    try:
        name = music.meta.song.title  # type: ignore
        if name is None:
            name = ""
    except AttributeError:
        name = ""

    return Multitrack(
        tracks=tracks,
        tempo=tempo_arr,
        # downbeat=music.downbeats if music.downbeats else None,
        beat_resolution=music.resolution,
        name=name,
    )


def to_pianoroll_representation(
    music: "Music",
    min_step: int = 1,
    binarized: bool = False,
    compact: bool = False,
) -> ndarray:
    """Return a Music object in pianoroll representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted pianoroll representation.
        size: L * D:
            - L for the sequence (note) length
            - D = 128
                the value in each dimension indicates the velocity

    """
    if compact and binarized:
        raise ValueError("`compact` and `binarized` must not be both True.")

    notes = []
    for track in music.tracks:
        notes.extend(track.notes)
    notes.sort(key=lambda x: x.time)

    if compact:
        if min_step > 1:
            raise NotImplementedError
        if not notes:
            return np.array([129], np.uint8)
        length = max((note.end for note in notes))
        compacted_pianoroll = np.empty(length, np.uint8)
        compacted_pianoroll.fill(129)
        for note in notes:
            compacted_pianoroll[note.time : note.end - 1] = note.pitch
        return compacted_pianoroll

    processor = PianoRollProcessor(min_step=min_step, binarized=binarized)
    return processor.encode(notes)
