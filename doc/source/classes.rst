=============
MusPy Classes
=============

These are the core classes in MusPy.


Music Class
============

The :class:`muspy.Music` class is the core element of MusPy. It is a universal container for symbolic music.

=============== ====================== ==================================== =========================
Attributes      Description            Type                                 Default
=============== ====================== ==================================== =========================
resolution      Time steps per beat    int                                  ``muspy.DEFAULT_RESOLUTION``
tempos          Tempo changes          list of :class:`muspy.Tempo`         []
key_signatures  Key signature changes  list of :class:`muspy.KeySignature`  []
time_signatures Time signature changes list of :class:`muspy.TimeSignature` []
downbeats       Downbeat positions     list of int                          []
lyrics          Lyrics                 list of :class:`muspy.Lyric`         []
annotations     Annotations            list of :class:`muspy.Annotation`    []
tracks          Music tracks           list of :class:`muspy.Track`         []
meta            Meta data              :class:`muspy.Metadata`              :class:`muspy.Metadata()`
=============== ====================== ==================================== =========================

.. Hint:: An example of a MusPy Music object as a YAML file is available `here <../examples.html>`__.


Tempo Class
===========

The :class:`muspy.Tempo` class is a container for tempo changes.

========== ======================================= ===== =======
Attributes Description                             Type  Default
========== ======================================= ===== =======
time       Start time of the tempo                 int
tempo      Tempo in qpm (quarter notes per minute) float
========== ======================================= ===== =======


KeySignature Class
==================

The :class:`muspy.KeySignature` class is a container for key signature changes.

========== ==================== ==== =======
Attributes Description          Type Default
========== ==================== ==== =======
time       Start time           int
root       Root (e.g., "C")     str
mode       Mode (e.g., "major") str
========== ==================== ==== =======


TimeSignature Class
===================

The :class:`muspy.TimeSignature` class is a container for time signature changes.

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

The :class:`muspy.Annotation` class is a container for annotations. In fact, `annotation` can hold any type of data.

========== ====================== ==== =======
Attributes Description            Type  Default
========== ====================== ==== =======
time       Start time             int
annotation Annotation of any type
========== ====================== ==== =======


Track Class
===========

The :class:`muspy.Note` class is a container for musical tracks.

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


Note Class
==========

The :class:`muspy.Note` class is a container for notes.

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


Metadata Class
==============

The :class:`muspy.Metadata` class is a container for meta data of a song.

============== ================== ========================= ===========================
Attributes     Description        Type                      Default
============== ================== ========================= ===========================
schema_version Schema version     str                       '0.0'
song           Song information   :class:`muspy.SongInfo`   :class:`muspy.SongInfo()`
source         Source information :class:`muspy.SourceInfo` :class:`muspy.SourceInfo()`
============== ================== ========================= ===========================


SongInfo Class
==============

The :class:`muspy.SongInfo` class is a container for song-related meta data.

========== ======================= =========== =======
Attributes Description             Type        Default
========== ======================= =========== =======
title      Song title              str
artist     Main artist of the song str
creators   Creators(s) of the song list of str []
========== ======================= =========== =======


SourceInfo  Class
=================

The :class:`muspy.SongInfo` class is a container for source-related meta data. This can be useful for dataset management.

========== =================================================== ==== =======
Attributes Description                                         Type Default
========== =================================================== ==== =======
filename   Name of the source file.                            str
collection Name of the collection                              str
format     Format of the source file (e.g., MIDI and MusicXML) str
copyright  Copyright notice of the source file.                str
========== =================================================== ==== =======
