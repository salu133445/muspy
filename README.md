MusPy
=====

MusPy is a Python library for symbolic music generation.


Features
--------

- Data I/O supports for common symbolic music formats and interfaces to other symbolic music libraries
- Manipulation, rendering, visualization and evaluation tools for symbolic music data
- Support for common music representations
- Dataset management for common datasets and local collections, with interfaces to PyTorch and TensorFlow


Installation
------------

Run the command `python setup.py install`.


Documentation
-------------

Documentation is provided as docstrings with the code. A HTML version is also available under `docs/` directory.


Development environment setup
-----------------------------

The development environment can be set up by running `pipenv install --dev` (make sure pipenv is installed properly, otherwise run `pip install pipenv`). This will install the linters (Pylint, Flake8 and mypy) and the formatter (black). The imports are sorted using VSCode Python extension (command: `python.sortImports`). The documentation is in NumPy style. Use of type hints are recommended.
