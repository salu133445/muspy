"""Utilities for event-based representations."""
import numpy as np
from ..processor import MidiEventProcessor


def to_event_representation(music, **kwargs):
    """Convert a :class:`muspy.Music` object to an event-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    min_step(optional):
        minimum quantification step
        decide how many ticks to be the basic unit (default = 1)
    tick_dim(optional):
        tick-shift event dimensions
        the maximum number of tick-shift (default = 100)
    velocity_dim(optional):
        velocity event dimensions
        the maximum number of quantized velocity (default = 32, max = 128)

    Returns
    ----------
    repr_seq:
        the note representation tokens
        Size: L * D:
        - L for the sequence (event) length
        - D = 1 {
            0-127: note-on event,
            128-255: note-off event,
            256-355(default):
                tick-shift event
                256 for one tick, 355 for 100 ticks
                the maximum number of tick-shift can be specified
            356-388 (default):
                velocity event
                the maximum number of quantized velocity can be specified
            }
    e.g.

    [C5 - - - E5 - - / G5 - - / /]
    ->
    [380, 60, 259, 188, 64, 258, 192, 256, 67, 258, 195, 257]

    """
    if not music.timing.is_symbolic:
        raise Exception("object is not symbolic", music.timing)
    note_seq = []
    for track in music.tracks:
        note_seq.extend(track.notes)
    note_seq.sort(key=lambda x: x.start)
    processor = MidiEventProcessor(**kwargs)
    repr_seq = processor.encode(note_seq)
    return np.array(repr_seq)
