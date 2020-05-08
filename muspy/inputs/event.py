"""Event-based representation input interface."""
from typing import Any

from ..classes import Track
from ..music import Music
from ..processor import MidiEventProcessor


def from_event_representation(data, **kwargs: Any) -> Music:
    """Return a Music object converted from an event-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in event-based representation to be converted.
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
        [380, 60, 259, 188, 64, 258, 192, 256, 67, 258, 195, 257]
        ->
        [C5 - - - E5 - - / G5 - - / /]
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
    music : :class:`muspy.Music` object
        Converted MusPy Music object. (Only Track - Note has the information)

    """
    processor = MidiEventProcessor(**kwargs)
    notes = processor.decode(data)
    return Music(tracks=[Track(notes=notes)], **kwargs)
