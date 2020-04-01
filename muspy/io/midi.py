"""MIDI I/O utilities."""
import pretty_midi


def parse_midi(music, filename, **kwargs):
    """
    Parse a MIDI file.

    Parameters
    ----------
    filename : str
        Filename of the MIDI file to be parsed.
    **kwargs:
        See :meth:`muspy.io.midi.parse_pretty_midi` for full documentation.
    """
    pm = pretty_midi.PrettyMIDI(filename)
    return parse_pretty_midi(music, pm, **kwargs)


def parse_pretty_midi(music, obj):
    """Parse a :class:`pretty_midi.PrettyMIDI` object."""
    if not isinstance(obj, pretty_midi.PrettyMIDI):
        raise TypeError(
            "Expect a file or a parsable object, but got {}.".format(type(obj))
        )
    # TODO: No implemented yet
    music.reset()
    return music
