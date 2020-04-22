===============
Timing in MusPy
===============

In MusPy, there are two supported timing systems: *metrical timing* and *absolute timing*. In a metrical timing system, time is stored in musically-meaningful unit (e.g., beats, quarter notes). For playback ability, additional resolution and tempo information is needed. In an absolute timing system, time is stored in seconds.

The timing system used in a :class:`muspy.Music` object is determined by the value of ``music.timing.is_symbolic``. If ``music.timing.is_symbolic=True``, the metrical timing system is used. If ``music.timing.is_symbolic=False``, the absolute timing system is used.


Metrical Timing
===============

In a metrical timing system, the smallest unit of time is a factor of a beat, which depends on the time signatures and set to a quarter note by default. We will refer to this smallest unit of time as a *time step*.

Here is the formula relating the symbolic and the absolute timing systems.

.. math:: absolute\_time = \frac{60 \times tempo}{resolution} \times symbolic\_time

Here, *resolution* is the number of time steps per beat and *tempo* is the current tempo (in beats per minute, or bpm). These two values are stored in a :class:`muspy.Music` object as ``music.timing.resolution`` and ``music.timing.tempos``.

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

When reading a MIDI file, ``music.timing.resolution`` is set to the pulses per quarter note (a.k.a., PPQ, PPQN, ticks per beat). When reading a MusicXML file, ``music.timing.resolution`` is set to the *division* attribute, which determines the number of divisions per quarter note.


Absolute Timing
===============

In an absolute timing system, the timing is in seconds. In this case, ``music.timing.resolution`` is simply ignored and ``music.timing.tempos`` serve as annotations only.
