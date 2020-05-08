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
    if music.timing.resolution is None:
        resolution = 1
        length = music.get_end_time()
    else:
        resolution = music.timing.resolution
        length = (music.get_end_time() // resolution + 1) * resolution

    # Tracks
    tracks = []
    for track in music.tracks:
        pianoroll = np.zeros((length, 128))
        for note in track.notes:
            pianoroll[
                note.start : note.end + 1, note.pitch  # type:ignore
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
    tempo_arr = 120.0 * np.ones(music.timing.get_end_time() + 1)
    qpm = 120.0
    position = 0
    for tempo in music.timing.tempos:
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
        downbeat=music.downbeats if music.downbeats else None,
        beat_resolution=resolution,
        name=name,
    )


def to_pianoroll_representation(music: "Music", **kwargs) -> np.ndarray:
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
    if not music.timing.is_metrical:
        raise Exception("object is not metrical", music.timing)
    note_seq = []
    for track in music.tracks:
        note_seq.extend(track.notes)

    min_step = 1
    if "min_step" in kwargs:
        min_step = kwargs["min_step"]
    note_seq.sort(key=lambda x: x.start)
    processor = PianoRollProcessor(min_step=min_step)
    repr_seq = processor.encode(note_seq)
    return np.array(repr_seq)
