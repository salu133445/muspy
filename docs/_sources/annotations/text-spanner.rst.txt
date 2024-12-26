============
Text Spanner
============

The :class:`muspy.TextSpanner` class is a container for text elements that span a certain duration
(text elements without duration should be stored as :class:`muspy.Text` objects). Text can be system-level,
where it applies to all parts in a song, or staff-level, where it only applies to a single part.

=========== ================================= ==== =======
Attributes  Description                       Type Default
=========== ================================= ==== =======
duration    Duration                          int
text        Text                              str
is_system   Whether it is system-level        bool False
style       Style of the text (e.g. 'tempo')  str
=========== ================================= ==== =======

.. autoclass:: muspy.TextSpanner
    :noindex:
    :inherited-members:
