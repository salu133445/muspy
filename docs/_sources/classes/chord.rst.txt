===========
Chord Class
===========

The :class:`muspy.Chord` class is a container for chords.

============ ================================= =================== =======
Attributes   Description                       Type                Default
============ ================================= =================== =======
time         Start time                        int
duration     Chord duration, in time steps     int
pitches      Note pitches as MIDI note numbers list of int (0-127) []
pitches_str  Note pitches as strings           list of str         []
velocity     Chord velocity                    int (0-127)
is_grace     Whether it is a grace chord       bool                False
============ ================================= =================== =======

.. Hint:: :class:`muspy.Chord` has a property `end` with setter and getter implemented, which can be handy sometimes.

.. autoclass:: muspy.Chord
    :noindex:
    :inherited-members:
