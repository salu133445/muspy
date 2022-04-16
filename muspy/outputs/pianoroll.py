"""Piano-roll output interface."""
from operator import attrgetter
from typing import TYPE_CHECKING, Union

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
        Music object to convert.

    Returns
    -------
    multitrack : :class:`pypianoroll.Multitrack`
        Converted Multitrack object.

    """
    length = music.get_end_time()

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
            program=track.program,
            is_drum=track.is_drum,
            name=track.name if track.name is not None else "",
            pianoroll=pianoroll,
        )
        tracks.append(track)

    # Tempos
    if not music.tempos:
        tempo_arr = None
    else:
        tempo_arr = np.full(length, 120.0)
        qpm = 120.0
        position = 0
        for tempo in music.tempos:
            tempo_arr[position : tempo.time] = qpm
            tempo_arr[tempo.time] = tempo.qpm
            position = tempo.time + 1
            qpm = tempo.qpm
        tempo_arr[position:] = qpm

    # Beats
    if not music.barlines:
        downbeat_arr = None
    else:
        downbeat_arr = np.zeros(length, bool)
        for barline in music.barlines:
            downbeat_arr[barline.time] = True

    # Downbeats
    if not music.beats:
        beat_arr = None
    else:
        beat_arr = np.zeros(length, bool)
        for beat in music.beats:
            beat_arr[beat.time] = True

    has_title = music.metadata is not None and music.metadata.title is not None

    try:
        # pylint: disable=unexpected-keyword-arg
        multitrack = Multitrack(
            name=music.metadata.title if has_title else None,
            resolution=music.resolution,
            tempo=tempo_arr,
            beat=beat_arr,
            downbeat=downbeat_arr,
            tracks=tracks,
        )
    except TypeError:
        multitrack = Multitrack(
            name=music.metadata.title if has_title else None,
            resolution=music.resolution,
            tempo=tempo_arr,
            downbeat=downbeat_arr,
            tracks=tracks,
        )
    return multitrack


def to_pianoroll_representation(
    music: "Music",
    encode_velocity: bool = True,
    dtype: Union[np.dtype, type, str] = None,
) -> ndarray:
    """Encode notes into piano-roll representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to encode.
    encode_velocity : bool, default: True
        Whether to encode velocities. If True, a binary-valued array
        will be return. Otherwise, an integer array will be return.
    dtype : np.dtype, type or str, optional
        Data type of the return array. Defaults to uint8 if
        `encode_velocity` is True, otherwise bool.

    Returns
    -------
    ndarray, shape=(?, 128)
        Encoded array in piano-roll representation.

    """
    if dtype is None:
        dtype = np.uint8 if encode_velocity else bool

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
        return np.zeros((0, 128), dtype)

    # Initialize the array
    length = max((note.end for note in notes))
    array = np.zeros((length + 1, 128), dtype)

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
