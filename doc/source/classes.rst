=============
MusPy Classes
=============

MusPy provides several classes for working with symbolic music. Here is an illustration of the relations between different MusPy classes.

.. image:: images/classes.svg


Music Class
============

The :class:`muspy.Music` class is the core element of MusPy. It is a universal container for symbolic music.

=============== ====================== ==================================== =========================
Attributes      Description            Type                                 Default
=============== ====================== ==================================== =========================
metadata        Metadata               :class:`muspy.Metadata`              :class:`muspy.Metadata()`
resolution      Time steps per beat    int                                  ``muspy.DEFAULT_RESOLUTION``
tempos          Tempo changes          list of :class:`muspy.Tempo`         []
key_signatures  Key signature changes  list of :class:`muspy.KeySignature`  []
time_signatures Time signature changes list of :class:`muspy.TimeSignature` []
downbeats       Downbeat positions     list of int                          []
lyrics          Lyrics                 list of :class:`muspy.Lyric`         []
annotations     Annotations            list of :class:`muspy.Annotation`    []
tracks          Music tracks           list of :class:`muspy.Track`         []
=============== ====================== ==================================== =========================

.. Hint:: An example of a MusPy Music object as a YAML file is available `here <../examples.html>`__.


Track Class
===========

The :class:`muspy.Track` class is a container for musical tracks. In MusPy, each track contains only one instrument.

=========== ======================== ================================= =======
Attributes  Description              Type                              Default
=========== ======================== ================================= =======
program     MIDI program number      int (0-127)                       0
is_drum     If it is a drum track    bool                              False
name        Track name               str
notes       Musical notes            list of :class:`muspy.Note`       []
chords      Chords                   list of :class:`muspy.Chord`      []
lyrics      Lyrics                   list of :class:`muspy.Lyric`      []
annotations Annotations              list of :class:`muspy.Annotation` []
=========== ======================== ================================= =======

(MIDI program number is based on General MIDI specification; see `here <https://www.midi.org/specifications/item/gm-level-1-sound-set>`__.)


Metadata Class
==============

The :class:`muspy.Metadata` class is a container for metadata.

=============== ========================= =========== =======
Attributes      Description               Type        Default
=============== ========================= =========== =======
schema_version  Schema version            str         '0.0'
title           Song title                str
creators        Creators(s) of the song   list of str []
copyright       Copyright notice          str
collection      Name of the collection    str
source_filename Name of the source file   str
source_format   Format of the source file str
=============== ========================= =========== =======


Tempo Class
===========

The :class:`muspy.Tempo` class is a container for tempos.

========== ======================================= ===== =======
Attributes Description                             Type  Default
========== ======================================= ===== =======
time       Start time of the tempo                 int
tempo      Tempo in qpm (quarter notes per minute) float
========== ======================================= ===== =======


KeySignature Class
==================

The :class:`muspy.KeySignature` class is a container for key signatures.

========== ==================== ==== =======
Attributes Description          Type Default
========== ==================== ==== =======
time       Start time           int
root       Root (e.g., "C")     str
mode       Mode (e.g., "major") str
========== ==================== ==== =======


TimeSignature Class
===================

The :class:`muspy.TimeSignature` class is a container for time signatures.

=========== =============================== ===== =======
Attributes  Description                     Type  Default
=========== =============================== ===== =======
time        Start time                      int
numerator   Numerator (e.g., "3" for 3/4)   int
denominator Denominator (e.g., "4" for 3/4) int
=========== =============================== ===== =======


Lyric Class
===========

The :class:`muspy.Lyric` class is a container for lyrics.

========== ====================================== ==== =======
Attributes Description                            Type Default
========== ====================================== ==== =======
time       Start time                             int
lyric      Lyric (sentence, word, syllable, etc.) str
========== ====================================== ==== =======


Annotation Class
================

The :class:`muspy.Annotation` class is a container for annotations. For flexibility, `annotation` can hold any type of data.

========== ====================== ==== =======
Attributes Description            Type  Default
========== ====================== ==== =======
time       Start time             int
annotation Annotation of any type
========== ====================== ==== =======


Note Class
==========

The :class:`muspy.Note` class is a container for musical notes.

========== ================================ =========== =======
Attributes Description                      Type        Default
========== ================================ =========== =======
start      Start time                       int
end        End time                         int
pitch      Note pitch as a MIDI note number int (0-127)
velocity   Note velocity                    int (0-127)
========== ================================ =========== =======

Note that :class:`muspy.Note` has a property `duration` with setter and getter implemented, which can be handy sometimes.


Chord Class
===========

The :class:`muspy.Chord` class is a container for chords.

========== ================================= =================== =======
Attributes Description                       Type                Default
========== ================================= =================== =======
start      Start time                        int
end        End time                          int
pitch      Note pitches as MIDI note numbers list of int (0-127) []
velocity   Chord velocity                    int (0-127)
========== ================================= =================== =======
