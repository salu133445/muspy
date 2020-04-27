"""Test for `muspy.representation`"""
import os.path

import muspy as msp

DIR = os.path.dirname(__file__)
TEST_MIDI_PATH = "tests/data/fur_elise.mid" # os.path.join(DIR, "data", "mono.mid")


def test_note_repr(path):
    temp = msp.read(path = path)
    repr_seq = temp.to_note_representation()
    print(repr_seq.shape)
    print(temp)
    re_temp = msp.from_note_representation(repr_seq)
    note_seq = []
    for track in temp.tracks:
        note_seq.extend(track.notes)
    note_seq.sort(key = lambda x:x.start)
    re_note_seq = re_temp.tracks[0].notes
    if len(re_note_seq) != len(note_seq):
        return False
    for i in range(len(re_note_seq)):
        x = note_seq[i]
        y = re_note_seq[i]
        if x.start != y.start or x.end != y.end or x.pitch != y.pitch or x.velocity != y.velocity:
            return False
    return True
def test_event_repr(path):
    temp = msp.read(path = path)
    repr_seq = temp.to_event_representation()
    print(repr_seq.shape)
    print(temp)
    re_temp = msp.from_event_representation(repr_seq)
    note_seq = []
    for track in temp.tracks:
        note_seq.extend(track.notes)
    note_seq.sort(key = lambda x:x.pitch)
    note_seq.sort(key = lambda x:x.start)
    re_note_seq = re_temp.tracks[0].notes
    re_note_seq.sort(key = lambda x:x.pitch)
    re_note_seq.sort(key = lambda x:x.start)
    if len(re_note_seq) != len(note_seq):
        return False
    for i in range(len(re_note_seq)):
        x = note_seq[i]
        y = re_note_seq[i]
        if x.start != y.start or x.end != y.end or x.pitch != y.pitch:
            print(i)
            return False
    return True
def test_mono_token_repr(path):
    temp = msp.read(path = path)
    repr_seq = temp.to_monotoken_representation()
    print(repr_seq.shape)
    print(temp)
    re_temp = msp.from_monotoken_representation(repr_seq)
    note_seq = []
    for track in temp.tracks:
        note_seq.extend(track.notes)
    note_seq.sort(key = lambda x:x.pitch)
    note_seq.sort(key = lambda x:x.start)
    re_note_seq = re_temp.tracks[0].notes
    re_note_seq.sort(key = lambda x:x.pitch)
    re_note_seq.sort(key = lambda x:x.start)
    if len(re_note_seq) != len(note_seq):
        return False
    
    for i in range(len(re_note_seq)):
        x = note_seq[i]
        y = re_note_seq[i]
        if x.start != y.start or x.end != y.end or x.pitch != y.pitch:
            return False
    return True
def test_pianoroll_repr(path):
    temp = msp.read(path = path)
    repr_seq = temp.to_pianoroll_representation()
    print(repr_seq.shape)
    print(temp)
    re_temp = msp.from_pianoroll_representation(repr_seq)
    note_seq = []
    for track in temp.tracks:
        note_seq.extend(track.notes)
    note_seq.sort(key = lambda x:x.pitch)
    note_seq.sort(key = lambda x:x.start)
    re_note_seq = re_temp.tracks[0].notes
    re_note_seq.sort(key = lambda x:x.pitch)
    re_note_seq.sort(key = lambda x:x.start)
    if len(re_note_seq) != len(note_seq):
        print(len(re_note_seq), len(note_seq))
        return False
    for i in range(len(re_note_seq)):
        x = note_seq[i]
        y = re_note_seq[i]
        if x.start != y.start or x.end != y.end or x.pitch != y.pitch or x.velocity != y.velocity:
            print(i)
            return False
    return True

print("test_note_repr:",test_note_repr(TEST_MIDI_PATH))
print("test_event_repr:",test_event_repr(TEST_MIDI_PATH)) 
# print("test_mono_token_repr:",test_mono_token_repr(TEST_MIDI_PATH))
print("test_pianoroll_repr:",test_pianoroll_repr(TEST_MIDI_PATH))