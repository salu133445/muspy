"""Piano-roll input interface."""
from operator import attrgetter
from typing import List

import numpy as np
from numpy import ndarray
from pypianoroll import Multitrack
from pypianoroll import Track as PypianorollTrack

from ..classes import Metadata, Note, Tempo, Track
from ..music import DEFAULT_RESOLUTION, Music


def _pianoroll_to_notes(
    array: ndarray, encode_velocity: bool, default_velocity: int
) -> List[Note]:
    binarized = array > 0
    diff = np.diff(binarized, axis=0, prepend=0, append=0)
    notes = []
    for i in range(128):
        boundaries = np.nonzero(diff[:, i])[0]
        for note_idx in range(len(boundaries) // 2):
            start = boundaries[2 * note_idx]
            end = boundaries[2 * note_idx + 1]
            if encode_velocity:
                velocity = array[start, i]
            else:
                velocity = default_velocity
            note = Note(
                time=start, duration=end - start, pitch=i, velocity=velocity,
            )
            notes.append(note)

    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    return notes


def parse_pypianoroll_track(
    track: PypianorollTrack, default_velocity: int = 64
) -> Track:
    """Return a Track object parsed from a Pypianoroll Track object.

    Parameters
    ----------
    track : :class:`pypianoroll.Track` object
        Pypianoroll Track object to convert.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    Returns
    -------
    :class:`muspy.Track` object
        Converted track.

    """
    # Convert piano roll to notes
    notes = _pianoroll_to_notes(
        track.pianoroll, not track.is_binarized, default_velocity
    )
    return Track(
        notes=notes,
        name=track.name if track.name else None,
        program=track.program,
        is_drum=track.is_drum,
    )


def from_pypianoroll(
    multitrack: Multitrack, default_velocity: int = 64
) -> Music:
    """Return a Music object converted from a Pypianoroll Multitrack object.

    Parameters
    ----------
    multitrack : :class:`pypianoroll.Multitrack` object
        Multitrack object to convert.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # Tempos
    tempo_change_timings = np.diff(multitrack.tempo, prepend=-1).nonzero()[0]
    tempos = [
        Tempo(time, qpm=multitrack.tempo[time])
        for time in tempo_change_timings
    ]
    # Tracks
    tracks = [
        parse_pypianoroll_track(track, default_velocity)
        for track in multitrack.tracks
    ]
    return Music(
        resolution=multitrack.beat_resolution,
        metadata=Metadata(title=multitrack.name) if multitrack.name else None,
        tempos=tempos,
        tracks=tracks,
    )


def from_pianoroll_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    encode_velocity: bool = True,
    default_velocity: int = 64,
) -> Music:
    """Decode pitch-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in piano-roll representation to decode. Will be casted to
        integer if not of integer type. If `encode_velocity` is True,
        will be casted to boolean if not of boolean type.
    resolution : int
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    program : int, optional
        Program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand
        Piano).
    is_drum : bool, optional
        A boolean indicating if it is a percussion track. Defaults to
        False.
    encode_velocity : bool
        Whether to encode velocities. Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.

    Returns
    -------
    :class:`muspy.Music` object
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if encode_velocity and not np.issubdtype(array.dtype, np.integer):
        array = array.astype(np.int)
    elif not encode_velocity and not np.issubdtype(array.dtype, np.bool):
        array = array.astype(np.bool)

    # Convert piano roll to notes
    notes = _pianoroll_to_notes(array, encode_velocity, default_velocity)

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
