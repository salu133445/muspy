===================================
Advanced Event-based Representation
===================================

The following class provides an advanced version of the event-based
representation with support for multiple tracks and providing a
vocabulary to map between integer IDs and human-readable tuples.
To avoid re-computing the vocabulary every time, and due to a large
number of arguments, only the processor API and not the function API
is provided.

.. autoclass:: muspy.AdvancedEventRepresentationProcessor
    :noindex:
    :inherited-members: