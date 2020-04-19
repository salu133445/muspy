===================
MusPy documentation
===================

MusPy is a Python package for processing symbolic music and working with common music datasets.

Features
========

- Data I/O for common formats (see `here <io.html>`_)
    - Read/write MIDI and MusicXML
    - Save/load JSON and YAML
    - Convert between objects of other packages
- Dataset management for common datasets (see `Dataset <datasets.html>`_)
    - Download from remote
    - Construct input pipeline
- Multiple representation supports (see `Representations <representations.html>`_)
    - Note-based representation
    - Event-based representation
    - Pianoroll representation

The core element of MusPy is the :class:`muspy.Music` class (see `Music Object <music.html>`_). Here is a system diagram of the package.

.. image:: images/system.svg
    :alt: System diagram

GitHub repository: https://github.com/icebergnlp/muspy

Contents
========

.. toctree::
    :maxdepth: 2

    music
    examples
    io
    representations
    datasets
    metrics
    visualization
    doc/index
