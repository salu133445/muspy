===============
Timing in MusPy
===============

In MusPy, the *metrical timing* is used. That is, time is stored in musically-meaningful unit (e.g., beats, quarter notes). For playback ability, additional resolution and tempo information is needed.


Metrical Timing
===============

In a metrical timing system, the smallest unit of time is a factor of a beat, which depends on the time signatures and set to a quarter note by default. We will refer to this smallest unit of time as a *time step*.

Here is the formula relating the metrical and the absolute timing systems.

.. math:: absolute\_time = \frac{60 \times tempo}{resolution} \times metrical\_time

Here, *resolution* is the number of time steps per beat and *tempo* is the current tempo (in beats per minute, or bpm). These two values are stored in a :class:`muspy.Music` object as ``music.resolution`` and ``music.tempos``.

The following are some illustrations of the relationships between time steps and time.

.. image:: images/timing_double_tempo.svg
    :align: center
    :width: 500px
.. image:: images/timing_half_tempo.svg
    :align: center
    :width: 500px
.. image:: images/timing_rubato.svg
    :align: center
    :width: 500px

When reading a MIDI file, ``music.resolution`` is set to the pulses per quarter note (a.k.a., PPQ, PPQN, ticks per beat). When reading a MusicXML file, ``music.resolution`` is set to the *division* attribute, which determines the number of divisions per quarter note.
