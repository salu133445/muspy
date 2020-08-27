===============
Representations
===============

MusPy supports several common representations for symbolic music. Here is a
comparison of them.

============== ========= ================ =================================================================
Representation Shape     Values           Default configurations
============== ========= ================ =================================================================
Pitch-based    *T* x 1   {0, 1, ..., 129} 128 note-ons, 1 hold, 1 rest (support only monophonic music)
Piano-roll     *T* x 128 {0, 1} or *R*    {0,1} for binary piano rolls; *R* for piano rolls with velocities
Event-based    *M* x 1   {0, 1, ..., 387} 128 note-ons, 128 note-offs, 100 tick shifts, 32 velocities
Note-based     *N* x 4   *N* or *R*       List of (*pitch*, *time*, *duration*, *velocity*) tuples
============== ========= ================ =================================================================

Note that *T*, *M*, and *N* denote the numbers of time steps, events and notes, respectively.


Pitch-based Representation
==========================

.. autofunction:: muspy.to_pitch_representation
    :noindex:

.. autofunction:: muspy.from_pitch_representation
    :noindex:


Pianoroll Representation
========================

.. autofunction:: muspy.to_pianoroll_representation
    :noindex:

.. autofunction:: muspy.from_pianoroll_representation
    :noindex:


Event-based Representation
==========================

.. autofunction:: muspy.to_event_representation
    :noindex:

.. autofunction:: muspy.from_event_representation
    :noindex:


Note-based Representation
=========================

.. autofunction:: muspy.to_note_representation
    :noindex:

.. autofunction:: muspy.from_note_representation
    :noindex:
