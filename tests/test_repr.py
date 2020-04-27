"""Test for `muspy.representation`"""
import os.path

import muspy as msp

DIR = os.path.dirname(__file__)
TEST_MIDI_PATH = "tests/data/mono.mid"  # os.path.join(DIR, "data", "mono.mid")

temp_object = msp.read(TEST_MIDI_PATH)
# note
repr_seq = temp_object.to_note_representation()
print(repr_seq.shape)
# mono_token
repr_seq = temp_object.to_mono_token_representation()
print(repr_seq.shape)
# event
repr_seq = temp_object.to_event_representation()
print(repr_seq.shape)
# pianoroll
repr_seq = temp_object.to_pianoroll_representation()
print(repr_seq.shape)
