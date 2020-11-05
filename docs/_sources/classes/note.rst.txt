==========
Note Class
==========

The :class:`muspy.Note` class is a container for musical notes.

========== ================================ =========== =======
Attributes Description                      Type        Default
========== ================================ =========== =======
time       Start time                       int
duration   Note duration, in time steps     int
pitch      Note pitch as a MIDI note number int (0-127)
velocity   Note velocity                    int (0-127)
========== ================================ =========== =======

.. Hint:: :class:`muspy.Note` has a property `end` with setter and getter implemented, which can be handy sometimes.

.. autoclass:: muspy.Note
    :noindex:
    :inherited-members:
