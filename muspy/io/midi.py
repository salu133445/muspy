"""MIDI I/O utilities."""
import pretty_midi


def parse_pretty_midi(music, obj):
    """Parse a :class:`pretty_midi.PrettyMIDI` object."""
    if not isinstance(obj, pretty_midi.PrettyMIDI):
        raise TypeError(
            "Expect a file or a parsable object, but got {}.".format(type(obj))
        )
    music.reset()
    # TODO: No implemented yet
    return music


def read_midi(music, filename, **kwargs):
    """Read a MIDI file into a :class:`muspy.Music` object.

    Parameters
    ----------
    filename : str
        Filename of the MIDI file to be parsed.
    **kwargs:
        See :meth:`muspy.io.parse_pretty_midi` for full documentation.
    """
    pm = pretty_midi.PrettyMIDI(filename)
    return parse_pretty_midi(music, pm, **kwargs)


def to_pretty_midi(music):
    """Convert a :class:`muspy.Music` object to a :class:`pretty_midi.PrettyMIDI`
    object."""
    pm = pretty_midi.PrettyMIDI()
    # TODO: No implemented yet
    return pm


def write_midi(music, filename, **kwargs):
    """Write a :class:`muspy.Music` object to a :class:`pretty_midi.PrettyMIDI`
    object."""
    pm = to_pretty_midi(music, **kwargs)
    pm.write(filename)
