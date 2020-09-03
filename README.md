MusPy
=====

[![Travis](https://img.shields.io/travis/com/salu133445/muspy)](https://travis-ci.com/salu133445/muspy)
[![Codecov](https://img.shields.io/codecov/c/github/salu133445/muspy)](https://codecov.io/gh/salu133445/muspy)
[![GitHub license](https://img.shields.io/github/license/salu133445/muspy)](https://github.com/salu133445/muspy/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/salu133445/muspy)](https://github.com/salu133445/muspy/releases)


MusPy is an open source Python library for symbolic music generation. It provides essential tools for developing a music generation system, including dataset management, data I/O, data preprocessing and model evaluation.


Features
--------

- Dataset management system for commonly used datasets with interfaces to PyTorch and TensorFlow.
- Data I/O for common symbolic music formats (e.g., MIDI, MusicXML and ABC) and interfaces to other symbolic music libraries (e.g., music21, mido, pretty_midi and Pypianoroll).
- Implementations of common music representations for music generation, including the pitch-based, the event-based, the piano-roll and the note-based representations.
- Model evaluation tools for music generation systems, including audio rendering, score and piano-roll visualizations and objective metrics.


Why MusPy
---------

A music generation pipeline usually consists of several steps: data collection, data preprocessing, model creation, model training and model evaluation. While some components need to be customized for each model, others can be shared across systems. For symbolic music generation in particular, a number of datasets, representations and metrics have been proposed in the literature. As a result, an easy-to-use toolkit that implements standard versions of such routines could save a great deal of time and effort and might lead to increased reproducibility.


Installation
------------

To install MusPy, please run `pip install muspy`. To build MusPy from source, please download the [source](https://github.com/salu133445/muspy/releases) and run `python setup.py install`.


Documentation
-------------

Documentation is available [here](https://salu133445.github.io/muspy) and as docstrings with the code.


Citing
------

Please cite the following paper if you use MusPy in a published work:

Hao-Wen Dong, Ke Chen, Julian McAuley, and Taylor Berg-Kirkpatrick, "MusPy: A Toolkit for Symbolic Music Generation," in _Proceedings of the 21st International Society for Music Information Retrieval Conference (ISMIR)_, 2020.


Disclaimer
----------

This is a utility library that downloads and prepares public datasets. We do not host or distribute these datasets, vouch for their quality or fairness, or claim that you have license to use the dataset. It is your responsibility to determine whether you have permission to use the dataset under the dataset's license.

If you're a dataset owner and wish to update any part of it (description, citation, etc.), or do not want your dataset to be included in this library, please get in touch through a GitHub issue. Thanks for your contribution to the community!
