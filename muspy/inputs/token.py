"""Token-based representation input interface."""
from ..music import Music


def from_monotoken_representation(data) -> Music:
    """Return a Music object converted from a monotoken-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in monotoken-based representation to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # TODO: Not implemented yet
    return Music()


def from_polytoken_representation(data) -> Music:
    """Return a Music object converted from a polytoken-based representation.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        Data in polytoken-based representation to be converted.

    Returns
    -------
    music : :class:`muspy.Music` object
        Converted MusPy Music object.

    """
    # TODO: Not implemented yet
    return Music()
