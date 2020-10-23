"""Note-based representation input interface."""
import statistics
from operator import attrgetter

import numpy as np
from numpy import ndarray

from ..classes import Note, Track, Tempo, TimeSignature
from ..music import DEFAULT_RESOLUTION, Music


def from_note_representation(
    array: ndarray,
    resolution: int = DEFAULT_RESOLUTION,
    program: int = 0,
    is_drum: bool = False,
    use_start_end: bool = False,
    encode_velocity: bool = True,
    encode_tempo: bool = True,
    default_velocity: int = 64,
    default_tempo: int = 120
) -> Music:
    """Decode note-based representation into a Music object.

    Parameters
    ----------
    array : ndarray
        Array in note-based representation to decode. Will be casted to
        integer if not of integer type.
    resolution : int
        Time steps per quarter note. Defaults to `muspy.DEFAULT_RESOLUTION`.
    program : int, optional
        Program number according to General MIDI specification [1].
        Acceptable values are 0 to 127. Defaults to 0 (Acoustic Grand
        Piano).
    is_drum : bool, optional
        A boolean indicating if it is a percussion track. Defaults to
        False.
    use_start_end : bool
        Whether to use 'start' and 'end' to encode the timing rather than
        'time' and 'duration'. Defaults to False.
    encode_velocity : bool
        Whether to encode note velocities. Defaults to True.
    encode_tempo: bool
        Whether to encode note tempo. Defaults to True.
    default_velocity : int
        Default velocity value to use when decoding if `encode_velocity` is
        False. Defaults to 64.
    default_tempo: int
        Default tempo value to use when decoding if `encode_tempo` is False.
        Defaults to 120

    Returns
    -------
    :class:`muspy.Music` object
        Decoded Music object.

    References
    ----------
    [1] https://www.midi.org/specifications/item/gm-level-1-sound-set

    """
    if not np.issubdtype(array.dtype, np.integer):
        array = array.astype(np.int)

    if encode_tempo:
        tempo_dict = {}
    notes = []
    velocity = default_velocity
    for note_tuple in array:

        if encode_velocity and encode_tempo:
            velocity = note_tuple[3]
            tempo = note_tuple[4]
        elif encode_tempo:
            tempo = note_tuple[3]
        elif encode_velocity:
            velocity = note_tuple[3]
        if encode_tempo:
            time = note_tuple[0]
            if tempo_dict.has_key(str(time)):
                tempo_dict[str(time)].append(tempo)
            else:
                tempo_dict[str(time)] = []
                tempo_dict[str(time)].append(tempo)

        if use_start_end:
            duration = note_tuple[2] - note_tuple[0]
        else:
            duration = note_tuple[2]

        notes.append(
            Note(
                time=note_tuple[0],
                pitch=note_tuple[1],
                duration=duration,
                velocity=velocity,
            )
        )

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Create the Track and Music objects
    track = Track(program=program, is_drum=is_drum, notes=notes)
    music = Music(resolution=resolution, tracks=[track])

    # Create Tempo object
    if encode_tempo:
        tempo_list = []
        for key, value in tempo_dict.items():
            time = int(key)
            qpm = int(statistics.mean(value))
            tempo = Tempo(time=time, qpm=qpm)
            tempo_list.append(tempo)
        tempo_list.sort(key=attrgetter("time"))
        music.tempo = tempo_list
    music.time_signatures = [TimeSignature(0, 4, 4)]
    return music
