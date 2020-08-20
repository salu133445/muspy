===========
Chord Class
===========

The :class:`muspy.Chord` class is a container for chords.

========== ================================= =================== =======
Attributes Description                       Type                Default
========== ================================= =================== =======
time       Start time                        int
duration   Chord duration, in time steps     int
pitch      Note pitches as MIDI note numbers list of int (0-127) []
velocity   Chord velocity                    int (0-127)
========== ================================= =================== =======

.. Hint:: :class:`muspy.Chord` has a property `end` with setter and getter implemented, which can be handy sometimes.
