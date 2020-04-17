========
Data I/O
========

MusPy provides three type of data I/O interface.

- Read to and write from MIDI or MusicXML formats
- Save to and load from native JSON and YAML formats
- Convert to and from objects in friend packages


Read/Write for common formats
=============================

MusPy supports read/write functions for MIDI nad MusicXML formats.

- MIDI: :func:`muspy.read_midi()` and :func:`muspy.write_midi()`
- MusicXML: and :func:`muspy.write_musicxml()`


Saving and Loading Music objects
================================

MusPy supports save/load functions for losslessly storing Music object.

- JSON: :func:`muspy.save_json()` and :func:`muspy.load_json()`
- YAML: :func:`muspy.save_yaml()` and :func:`muspy.load_yaml()`


CConvert to and from objects of friend packages
===============================================

MusPy supports conversion between :class:`muspy.Music` objects and objects from
friend packages, such as pretty_midi and pypianoorll.

- pretty_midi: :func:`muspy.from_pretty_midi()` and :func:`muspy.to_pretty_midi()`
- pypianoroll: :func:`muspy.from_pypianorll()` and :func:`muspy.to_pypianorll()`
