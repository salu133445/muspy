===========
Music Class
===========

The :class:`muspy.Music` class is the core element of MusPy. It is a universal container for symbolic music.

=============== ====================== ==================================== =========================
Attributes      Description            Type                                 Default
=============== ====================== ==================================== =========================
metadata        Metadata               :class:`muspy.Metadata`              :class:`muspy.Metadata()`
resolution      Time steps per beat    int                                  ``muspy.DEFAULT_RESOLUTION``
tempos          Tempo changes          list of :class:`muspy.Tempo`         []
key_signatures  Key signature changes  list of :class:`muspy.KeySignature`  []
time_signatures Time signature changes list of :class:`muspy.TimeSignature` []
beats           Beats                  list of :class:`muspy.Beat`          []
lyrics          Lyrics                 list of :class:`muspy.Lyric`         []
annotations     Annotations            list of :class:`muspy.Annotation`    []
tracks          Music tracks           list of :class:`muspy.Track`         []
=============== ====================== ==================================== =========================

.. Hint:: An example of a MusPy Music object as a YAML file is available `here <../examples.html>`__.

.. autoclass:: muspy.Music
    :noindex:
    :inherited-members:
