========
Data I/O
========

MusPy provides three type of data I/O interface.

- Reading and writing with MIDI and MusicXML
- Saving and loading with JSON and YAML
- Conversion between objects in other packages

.. image:: images/io.svg
    :align: center
    :width: 300px


Reading and Writing
===================

MusPy supports reading and writing with MIDI nad MusicXML formats.

- **MIDI**: :func:`muspy.read_midi()` and :func:`muspy.write_midi()`
- **MusicXML**: :func:`muspy.read_musicxml()` and :func:`muspy.write_musicxml()`


Saving and Loading
==================

MusPy supports save/load functions for losslessly storing Music object.

- **JSON**: :func:`muspy.save_json()` and :func:`muspy.load_json()`
- **YAML**: :func:`muspy.save_yaml()` and :func:`muspy.load_yaml()`

.. Hint:: An example of a MusPy Music object saved as a YAML file is available `here <examples.html>`_.

JSON/YAML Schemas
-----------------

MusPy provides schemas in JSON_ and YAML_ formats. These can be used to validate a JSON or YAML file for the Music object.

.. _JSON: https://github.com/icebergnlp/muspy/blob/master/muspy/schemas/music.schema.json
.. _YAML: https://github.com/icebergnlp/muspy/blob/master/muspy/schemas/music.schema.yaml


Interface with other packages
=============================

MusPy supports conversion between :class:`muspy.Music` objects and objects from
other packages, such as :class:`pretty_midi.PrettyMIDI` and :class:`pypianoroll.Multitrack` objects.

- **pretty_midi**: :func:`muspy.from_pretty_midi()` and :func:`muspy.to_pretty_midi()`
- **Pypianoroll**: :func:`muspy.from_pypianoroll()` and :func:`muspy.to_pypianoroll()`
