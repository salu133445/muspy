"""ABC input interface."""
import warnings
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import List, Union

import music21

from ..classes import (
    Annotation,
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SourceInfo,
    Tempo,
    TimeSignature,
    Timing,
    Track,
)
from ..music import Music

"""
abc basic helper functions
"""
def abc_get_notes(score):
    re = []
    for i in score.notesAndRests:
        if isinstance(i, music21.note.Note):
            dur = float(i.duration.quarterLength)
            ofs = float(i.offset)
            if int(round(dur * 24)) != dur * 24 or int(round(ofs * 24)) != ofs * 24:
                print("Warning: abc conversion offset tick error!")
                print(dur, ofs)
            re.append([i.pitch.midi, dur * 24, ofs * 24])
    return re

def abc_get_chords(score):
    re = []
    for i in score.notesAndRests:
        if isinstance(i, music21.harmony.ChordSymbol):
            ofs = float(i.offset)
            for j in i.notes: 
                dur = float(j.duration.quarterLength)
                if int(round(dur * 24)) != dur * 24 or int(round(ofs * 24)) != ofs * 24:
                    print("Warning: abc conversion offset tick error!")
                    print(dur, ofs)
                re.append([j.pitch.midi, dur * 24, ofs * 24])
    return re

def abc_get_keys(score):
    re = []
    for i in score.getKeySignatures():
        ofs = float(i.offset)
        if int(round(ofs * 24)) != ofs * 24:
            print("Warning: abc conversion offset tick error!")
            print(ofs)
        re.append([i,  ofs * 24])
    return re
               
def abc_get_times(score):
    re = []
    for i in score.getTimeSignatures():
        ofs = float(i.offset)
        if int(round(ofs * 24)) != ofs * 24:
            print("Warning: abc conversion offset tick error!")
            print(ofs)
        re.append([i,  ofs * 24])
    return re
            

def read_abc_music21(
    path: Union[str, Path], min_step = 24, except_file = ""):
    """Read a abc file into a Music object using music21 as backend.

    Parameters
    ----------
    path : str or Path
        Path to the MIDI file to be read.

    Returns
    -------
    :class:`muspy.Music` object list
        Converted MusPy Music object list.

    """
    abc_file_list = []
    scores = music21.converter.parse(path)
    for score in scores[0:]:
        score = score.flat
        time = 0
        # Create a list to store converted tracks
        tracks = []
        # Create a list to store track names
        notes = abc_get_notes(score)
        chords = abc_get_chords(score)
        key_changes = abc_get_keys(score)
        time_changes = abc_get_times(score)
        key_changes = [
            KeySignature(int(k[1]), str(k[0].tonic).replace("-","b"), str(k[0].mode)) 
            for k in key_changes
        ]
        time_changes = [
            TimeSignature(int(t[1]), int(t[0].numerator), int(t[0].denominator)) 
            for t in time_changes
        ]
        notes = [
            Note(start = int(note[2]), end = int(note[2] + note[1]), pitch = int(note[0]), velocity = int(100))
            for note in notes
        ]
        chords = [
            Note(start = int(note[2]), end = int(note[2] + note[1]), pitch = int(note[0]), velocity = int(100))
            for note in chords
        ]
        melody_track = Track(name = "Melody", notes = notes)
        chord_track = Track(name = "Chord", notes = chords)
        tracks.append(melody_track)
        tracks.append(chord_track)
        abc_file_list.append(
            Music(
                meta = MetaData(source=SourceInfo(filename = re.sub('[^a-zA-Z]','',score.metadata.title), copyright = "Nottingham Database")), 
                timing=Timing(resolution=24, tempos=[Tempo(0, 120.0)]),
                key_signatures=key_changes, 
                time_signatures=time_changes,
                tracks=tracks)
        )

        # print(key_changes)

    return abc_file_list





    
