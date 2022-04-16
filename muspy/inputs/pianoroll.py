"""Piano-roll input interface."""
from operator import attrgetter
from typing import List

import numpy as np
from numpy import ndarray
from pypianoroll import Multitrack
from pypianoroll import Track as PypianorollTrack

from ..classes import (
    DEFAULT_VELOCITY,
    Barline,
    Beat,
    Metadata,
    Note,
    Tempo,
    Track,
)
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
                time=int(start),
                pitch=i,
                duration=int(end - start),
                velocity=int(velocity),
            )
            notes.append(note)

    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    return notes


def from_pypianoroll_track(
    track: PypianorollTrack, default_velocity: int = DEFAULT_VELOCITY
) -> Track:
    """Return a Pypianoroll Track object as a Track object.

    Parameters
    ----------
    track : :class:`pypianoroll.Track`
        Pypianoroll Track object to convert.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding.

    Returns
    -------
    :class:`muspy.Track`
        Converted track.

    """
    # Convert piano roll to notes
    notes = _pianoroll_to_notes(
        track.pianoroll, track.pianoroll.dtype == np.bool_, default_velocity
    )
    return Track(
        notes=notes,
        name=track.name if track.name else None,
        program=track.program,
        is_drum=track.is_drum,
    )


def from_pypianoroll(
    multitrack: Multitrack, default_velocity: int = DEFAULT_VELOCITY
) -> Music:
    """Return a Pypianoroll Multitrack object as a Music object.

    Parameters
    ----------
    multitrack : :class:`pypianoroll.Multitrack`
        Pypianoroll Multitrack object to convert.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding.

    Returns
    -------
    :class:`muspy.Music`
        Converted MusPy Music object.

    """
    # Metadata
    metadata = Metadata(
        title=multitrack.name if multitrack.name else None,
        source_format="pypianoroll",
    )

    # Tempos
    if multitrack.tempo is not None:
        tempo_change_timings = np.diff(multitrack.tempo, prepend=-1).nonzero()[
            0
        ]
        tempos = [
            Tempo(time, qpm=float(multitrack.tempo[time]))
            for time in tempo_change_timings
        ]
    else:
        tempos = None

    # Beats
    if hasattr(multitrack, "beat") and multitrack.beat is not None:
        beats = [
            Beat(time=int(time)) for time in np.nonzero(multitrack.beat)[0]
        ]
    else:
        beats = None

    # Barlines
    if multitrack.downbeat is not None:
        barlines = [
            Barline(time=int(time))
            for time in np.nonzero(multitrack.downbeat)[0]
        ]
    else:
        barlines = None

    # Tracks
    if multitrack.tracks is not None:
        tracks = [
            from_pypianoroll_track(track, default_velocity)
            for track in multitrack.tracks
        ]
    else:
        tracks = None

    return Music(
        resolution=int(multitrack.resolution),
        metadata=metadata,
        tempos=tempos,
        barlines=barlines,
        beats=beats,
        tracks=tracks,
    )


def from_pianoroll_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    encode_velocity: bool = True,
    default_velocity: int = DEFAULT_VELOCITY,
) -> Music:
    """Decode piano-roll representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in piano-roll representation to decode.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    program : int, default: 0 (Acoustic Grand Piano)
        Program number, according to General MIDI specification [1].
        Valid values are 0 to 127.
    is_drum : bool, default: False
        Whether it is a percussion track.
    encode_velocity : bool, default: True
        Whether to encode velocities.
    default_velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        Default velocity value to use when decoding. Only used when
        `encode_velocity` is True.

    Returns
    -------
    :class:`muspy.Music`
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if encode_velocity and not np.issubdtype(array.dtype, np.integer):
        raise TypeError(
            "Array must be of type int when `encode_velocity` is True."
        )
    if not encode_velocity and not np.issubdtype(array.dtype, bool):
        raise TypeError(
            "Array must be of type bool when `encode_velocity` is False."
        )

    # Convert piano roll to notes
    notes = _pianoroll_to_notes(array, encode_velocity, default_velocity)

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    return music
