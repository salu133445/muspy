"""Event-based representation input interface."""
from ..music import Music


def from_event_representation(data) -> Music:
    """Return a Music object converted from an event-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in event-based representation to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # TODO: Not implemented yet
    return Music()
