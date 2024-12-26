====
Text
====

The :class:`muspy.Text` class is a container for text elements
(text elements that span a certain duration should be stored as :class:`muspy.TextSpanner` objects).
Text can be system-level, where it applies to all parts in a song, or staff-level,
where it only applies to a single part.

=========== ================================= ==== =======
Attributes  Description                       Type Default
=========== ================================= ==== =======
text        Text                              str
is_system   Whether it is system-level        bool False
style       Style of the text (e.g. 'tempo')  str
=========== ================================= ==== =======

.. autoclass:: muspy.Text
    :noindex:
    :inherited-members:
