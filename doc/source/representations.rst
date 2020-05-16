===============
Representations
===============

MusPy supports several common representations for symbolic music. Here is a
comparison.

============== ========= ================ ================================================================
Representation Shape     Values           Default configurations
============== ========= ================ ================================================================
Note-based     *N* x 4   *N* or *R*+      List of (*pitch*, *start_time*, *end_time*, *velocity*) tuples
Pitch-based    *T* x 1   {0, 1, ..., 129} 128 note-ons, 1 hold, 1 rest (support only monophonic music)
Event-based    *T* x 1   {0, 1, ..., 387} 128 note-ons, 128 note-offs, 100 tick shifts, 32 velocities
Pianoroll      *T* x 128 {0, 1} or *R*+   {0,1} for binary pianorolls; *R*+ for pianorolls with velocities
============== ========= ================ ================================================================

Note that *T* and *N* denote the numbers of time steps and notes, respectively.


Event Representation
====================

.. autofunction:: muspy.from_event_representation
    :noindex:

.. autofunction:: muspy.to_event_representation
    :noindex:


Note Representation
===================

.. autofunction:: muspy.from_note_representation
    :noindex:

.. autofunction:: muspy.to_note_representation
    :noindex:


Monotoken Representation
========================

.. autofunction:: muspy.from_monotoken_representation
    :noindex:

.. autofunction:: muspy.to_monotoken_representation
    :noindex:


Pianoroll Representation
========================

.. autofunction:: muspy.from_pianoroll_representation
    :noindex:

.. autofunction:: muspy.to_pianoroll_representation
    :noindex:
