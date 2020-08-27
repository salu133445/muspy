===============
Representations
===============

MusPy supports several common representations for symbolic music. Here is a
comparison of them.

============== ========= ================ =================================================================
Representation Shape     Values           Default configurations
============== ========= ================ =================================================================
Pitch-based    *T* x 1   {0, 1, ..., 129} 128 note-ons, 1 hold, 1 rest (support only monophonic music)
Piano-roll     *T* x 128 {0, 1} or *N*    {0,1} for binary piano rolls; *N* for piano rolls with velocities
Event-based    *M* x 1   {0, 1, ..., 387} 128 note-ons, 128 note-offs, 100 tick shifts, 32 velocities
Note-based     *N* x 4   *N*              List of (*pitch*, *time*, *duration*, *velocity*) tuples
============== ========= ================ =================================================================

Note that *T*, *M*, and *N* denote the numbers of time steps, events and notes, respectively.

MusPy's representation module supports two types of two APIs---Functional API and Processor API. Take the pitch-based representation for example.

- The Functional API provide two functions:
  - :func:`muspy.to_pitch_representation`: Convert a Music object into pitch-based representation
  - :func:`muspy.from_pitch_representation`: Return a Music object converted from pitch-based representation
- The Processor API provides the class :class:`muspy.PitchRepresentationProcessor`, which provides two methods:
  - :meth:`muspy.PitchRepresentationProcessor.encode`: Convert a Music object into pitch-based representation
  - :meth:`muspy.PitchRepresentationProcessor.decode`: Return a Music object converted from pitch-based representation


.. toctree::
    :titlesonly:

    pitch
    pianoroll
    event
    note
