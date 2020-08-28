========
Data I/O
========

MusPy provides three type of data I/O interfaces.

- Common symbolic music formats (MIDI, MusicXML and ABC)
- MusPy's native JSON and YAML formats
- Other symbolic music libraries (music21, mido, pretty_midi and Pypianoroll)


Read and Write
==============

MusPy supports reading and writing with MIDI, MusicXML and ABC formats.

- **MIDI**: :func:`muspy.read_midi()` and :func:`muspy.write_midi()`
- **MusicXML**: :func:`muspy.read_musicxml()` and :func:`muspy.write_musicxml()`
- **ABC**: :func:`muspy.read_abc()` and :func:`muspy.write_abc()`


Save and Load
=============

MusPy supports save/load functions for losslessly storing Music object.

- **JSON**: :func:`muspy.save_json()` and :func:`muspy.load_json()`
- **YAML**: :func:`muspy.save_yaml()` and :func:`muspy.load_yaml()`

.. Hint:: An example of a MusPy Music object saved as a YAML file is available `here <examples.html>`_.

.. Note:: MusPy provides schemas in JSON_ and YAML_ formats. These can be used to validate a JSON or YAML file for the Music object.

.. _JSON: https://github.com/icebergnlp/muspy/blob/master/muspy/schemas/music.schema.json
.. _YAML: https://github.com/icebergnlp/muspy/blob/master/muspy/schemas/music.schema.yaml


Interfaces to other symbolic music packages
===========================================

MusPy supports conversions between :class:`muspy.Music` objects and objects from other packages.

- **Music21**: :func:`muspy.from_music21()` and :func:`muspy.to_music21()`
- **mido**: :func:`muspy.from_mido()` and :func:`muspy.to_mido()`
- **pretty_midi**: :func:`muspy.from_pretty_midi()` and :func:`muspy.to_pretty_midi()`
- **Pypianoroll**: :func:`muspy.from_pypianoroll()` and :func:`muspy.to_pypianoroll()`
