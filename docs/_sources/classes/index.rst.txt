=============
MusPy Classes
=============

.. toctree::
    :hidden:

    music
    track
    metadata
    tempo
    key-signature
    time-signature
    lyric
    annotation
    note
    chord

MusPy provides several classes for working with symbolic music. Here is an illustration of the relations between different MusPy classes.

.. image:: ../images/classes.svg


Base Class
==========

All MusPy classes inherit from the :class:`muspy.Base` class. A :class:`muspy.Base` object supports the following operations.

- :meth:`muspy.Base.to_ordered_dict`: convert the content into an ordered dictionary
- :meth:`muspy.Base.from_dict` (class method): create a MusPy object of a certain class
- :meth:`muspy.Base.print`: show the content in a YAML-like format
- :meth:`muspy.Base.validate`: validate the data stored in an object
- :meth:`muspy.Base.is_valid`: return a boolean indicating if the stored data is valid
- :meth:`muspy.Base.adjust_time`: adjust the timing of an object


ComplexBase Class
=================

MusPy classes that contains list attributes also inherit from the :class:`muspy.ComplexBase` class. A :class:`muspy.ComplexBase` object supports the following operations.

- :meth:`muspy.ComplexBase.append`: append an object to the corresponding list
- :meth:`muspy.ComplexBase.remove_invalid`: remove invalid items from the lists
- :meth:`muspy.ComplexBase.sort`: sort the lists
- :meth:`muspy.ComplexBase.remove_duplicate`: remove duplicate items from the lists
