"""Event-based representation output interface."""
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy import ndarray

from ..processor import MidiEventProcessor

if TYPE_CHECKING:
    from ..music import Music


def to_event_representation(
    music: "Music", min_step: int = 1, **kwargs: Any
) -> ndarray:
    """Return a Music object in event-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.
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
    -------
    array : :class:`numpy.ndarray`
        Converted event-based representation.
        size: L * D:
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
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)
    notes.sort(key=lambda x: x.start)
    processor = MidiEventProcessor(min_step=min_step, **kwargs)
    return np.array(processor.encode(notes))
