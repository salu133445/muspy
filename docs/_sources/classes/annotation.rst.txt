================
Annotation Class
================

The :class:`muspy.Annotation` class is a container for annotations. For flexibility, `annotation` can hold any type of data.  An annotation object can be stored in either a :class:`muspy.Music` or a :class:`muspy.Track` object as a global or track-specific annotation, respectively.

========== ====================== ==== =======
Attributes Description            Type  Default
========== ====================== ==== =======
time       Start time             int
annotation Annotation of any type
========== ====================== ==== =======

.. autoclass:: muspy.Annotation
    :noindex:
    :inherited-members:
