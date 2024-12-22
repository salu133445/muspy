=============
Trill Spanner
=============

The :class:`muspy.TrillSpanner` class is a container for trills that span a certain duration
(trills that only apply to a single note should be stored as :class:`muspy.Ornament` objects).

=========== ==================================== ==== =======
Attributes  Description                          Type Default
=========== ==================================== ==== =======
duration    Duration                             int
subtype     Subtype                              str  'trill'
ornament    Ornament associated with the trill   str
=========== ==================================== ==== =======

.. autoclass:: muspy.TrillSpanner
    :noindex:
    :inherited-members:
