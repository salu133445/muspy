===========
Track Class
===========

The :class:`muspy.Track` class is a container for music tracks. In MusPy, each track contains only one instrument.

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
