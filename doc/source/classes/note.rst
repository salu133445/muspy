==========
Note Class
==========

The :class:`muspy.Note` class is a container for musical notes.

========== =============================================== =========== =======
Attributes Description                                     Type        Default
========== =============================================== =========== =======
time       Start time                                      int
duration   Note duration, in time steps                    int
pitch      Note pitch as a MIDI note number                int (0-127)
pitch_str  Note pitch as a string                          str
velocity   Note velocity                                   int (0-127)
is_grace   Whether it is a grace note                      bool        False
notations  Note-specific annotations, like articulations   list
========== =============================================== =========== =======

.. Hint:: :class:`muspy.Note` has a property `end` with setter and getter implemented, which can be handy sometimes.

.. Hint:: :class:`muspy.Note` has a `notations` attribute, which is useful for storing annotations that belong to a specific note.

.. autoclass:: muspy.Note
    :noindex:
    :inherited-members:
