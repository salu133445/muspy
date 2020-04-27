"""Token-based representation output interface."""
from numpy import ndarray


def to_monotoken_representation(music: "Music") -> ndarray:
    """Return a Music object in monotoken-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted monotoken-based representation.

    """
    # TODO: Not implemented yet
    return ndarray()


def to_polytoken_representation(music: "Music") -> ndarray:
    """Return a Music object in polytoken-based representation.

    Parameters
    ----------
    music : :class:`muspy.Music`
        MusPy Music object to be converted.

    Returns
    -------
    array : :class:`numpy.ndarray`
        Converted polytoken-based representation.

    """
    # TODO: Not implemented yet
    return ndarray()
