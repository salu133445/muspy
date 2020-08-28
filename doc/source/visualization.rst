=============
Visualization
=============

MusPy supports two visualization tools. Both use Matplotlib as the backend for flexibility.


Piano-roll Visualization
========================

The piano-roll visualization is made possible with the `Pypianoroll <https://salu133445.github.io/pypianoroll/>`_ library.

.. image:: images/pianoroll.png
    :align: center
    :width: 500px

.. autofunction:: muspy.show_pianoroll
    :noindex:


Score Visualization
===================

The score visualization is made possible with the `Bravura <https://github.com/steinbergmedia/bravura>`_ font.

.. image:: images/score.png
    :align: center
    :width: 500px

.. autofunction:: muspy.show_score
    :noindex:

.. autofunction:: muspy.ScorePlotter
    :noindex:
