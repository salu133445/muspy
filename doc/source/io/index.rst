=======================
Input/Output Interfaces
=======================

MusPy provides three type of data I/O interfaces.

- Common symbolic music formats: ``muspy.read_*`` and ``muspy.write_*``
- MusPy's native JSON and YAML formats: ``muspy.load_*`` and ``muspy.save_*``
- Other symbolic music libraries: ``muspy.from_*`` and ``muspy.to_*``

Here is a list of the supported interfaces.

.. toctree::
    :titlesonly:

    midi
    musicxml
    abc
    json
    yaml
    mido
    music21
    pretty_midi
    pypianoroll
