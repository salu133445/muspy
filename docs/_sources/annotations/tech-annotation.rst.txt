====================
Technical Annotation
====================

The :class:`muspy.TechAnnotation` class is a container for technical annotations (such as ``mute`` or ``open`` directives).
Like its parent class :class:`muspy.Text`, a technical annotation can be system-level, where it applies to all parts in a song,
or staff-level, where it only applies to a single part.

=========== ================================= ==== =======
Attributes  Description                       Type Default
=========== ================================= ==== =======
text        Text                              str
tech_type   Type of technical annotation      str
is_system   Whether it is system-level        bool False
style       Style of the text (e.g. 'tempo')  str
=========== ================================= ==== =======

.. autoclass:: muspy.TechAnnotation
    :noindex:
    :inherited-members:
