"""Piano-roll output interface."""
from operator import attrgetter
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray
from pypianoroll import Multitrack, Track

from ..classes import DEFAULT_VELOCITY

if TYPE_CHECKING:
    from ..music import Music


def to_pypianoroll(music: "Music") -> Multitrack:
    """Return a Music object as a Multitrack object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to convert.

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
            if note.velocity is not None:
                pianoroll[note.time : note.end, note.pitch] = note.velocity
            else:
                pianoroll[note.time : note.end, note.pitch] = DEFAULT_VELOCITY
        track = Track(
            pianoroll,
            track.program,
            track.is_drum,
            track.name if track.name is not None else "",
        )
        tracks.append(track)

    # Tempos
    last_tempo_time = max((tempo.time for tempo in music.tempos))
    tempo_arr = 120.0 * np.ones(last_tempo_time + 1)
    qpm = 120.0
    position = 0
    for tempo in music.tempos:
        tempo_arr[position : tempo.time] = qpm
        tempo_arr[tempo.time] = tempo.qpm
        position = tempo.time + 1
        qpm = tempo.qpm

    if music.metadata is not None:
        name = music.metadata.title if music.metadata.title is not None else ""

    return Multitrack(
        tracks=tracks,
        tempo=tempo_arr,
        # downbeat=music.downbeats if music.downbeats else None,
        beat_resolution=music.resolution,
        name=name,
    )


def to_pianoroll_representation(
    music: "Music", encode_velocity: bool = True
) -> ndarray:
    """Encode notes into piano-roll representation.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to encode.
    encode_velocity : bool
        Whether to encode velocities. If True, a binary-valued array will be
        return. Otherwise, an integer array will be return. Defaults to
        True.

    Returns
    -------
    ndarray, dtype=uint8 or bool, shape=(?, 128)
        Encoded array in piano-roll representation.

    """
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes are found
    if not notes:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    if not notes:
        return np.zeros((1, 128), np.uint8)

    # Initialize the array
    length = max((note.end for note in notes))
    if encode_velocity:
        array = np.zeros((length + 1, 128), np.uint8)
    else:
        array = np.zeros((length + 1, 128), np.bool)

    # Encode notes
    for note in notes:
        if note.velocity is not None:
            if encode_velocity:
                array[note.time : note.end, note.pitch] = note.velocity
            else:
                array[note.time : note.end, note.pitch] = note.velocity > 0
        elif encode_velocity:
            array[note.time : note.end, note.pitch] = DEFAULT_VELOCITY
        else:
            array[note.time : note.end, note.pitch] = True

    return array
