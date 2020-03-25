# A processor for one_hot note_based midi processing 
# RSnut 2020.3.15
import pretty_midi as pyd
import numpy as np
import os
import random
# from loader.chordloader import Chord_Loader
import copy

class OnehotProcessor:
    def __init__(self, dataset_name, min_step = 0.5 / 6):
        self.dataset_name = dataset_name
        self.min_step = min_step
        self.hold_state = 128
        self.rest_state = 129
    def encode(self, note_seq, c_bias = 0.0):
        # convert the midi note sequence into one hot matrix
        # input: L x 128 | output: T x 130  
        # TODO: tempo changes issue
        # 130 one hot vectors 
        # 0-127 for pitch
        # 128 for hold 129 for rest
        # c_bias=  1.0 / 960 for Irish Dataset
        # c_bias = 0.0 for Nottingham Dataset
        pitch_file = []
        cst = note_seq[0].start - c_bias
        cet = note_seq[0].end
        # first note starts > 0
        if cst > 0:
            steps = int(round((cst) / self.min_step))
            pitch_file.extend([self.rest_state] * steps)
        cst = 0.0
        cet = note_seq[0].start - c_bias
        for note in note_seq:
            # print(abs(note.start - c_bias - cet))
            if note.start - cet - c_bias >= -0.0001:
                den_step = int(round((note.start - cet - c_bias) / self.min_step))
                pitch_file.extend([self.rest_state] * den_step)
                cst = note.start - c_bias
                cet = note.end
                add_pitch = note.pitch
                steps = int(round((cet - cst) / self.min_step))
                if steps > 0:
                    pitch_file.extend([add_pitch])
                    pitch_file.extend([self.hold_state] * (steps - 1))
            elif note.start - c_bias <= cst:
                continue
        return pitch_file
    def decode(self, onehot_seq, output_dir = None):
        # convert the one hot maxtrix into midi_file, if output_dir is not None, it will output the midi
        # input: T x 130 | output: L x 128 
        # TODO: tempo changes issue
        # 130 one hot vectors 
        # 0-127 for pitch
        # 128 for hold 129 for rest
        local_duration = 0
        time_shift = 0.0
        local_duration = 0
        prev = self.rest_state
        pitch_file = []
        for note in onehot_seq:
            note = int(note)
            if note < 0 or note > 129:
                continue
            if note == self.hold_state:
                local_duration += 1
            else:
                if prev != self.rest_state:
                    i_note = pyd.Note(velocity = 100, pitch = prev, 
                        start = time_shift, end = time_shift + local_duration * self.min_step)
                    pitch_file.append(i_note)
                prev = note
                time_shift += local_duration * self.min_step
                local_duration = 1
        if prev != self.rest_state:
            i_note = pyd.Note(velocity = 100, pitch = prev, 
                        start = time_shift, end = time_shift + local_duration * self.min_step)
            pitch_file.append(i_note)
        if output_dir is not None:
            gen_midi = pyd.PrettyMIDI()
            melodies = pyd.Instrument(program = pyd.instrument_name_to_program('Acoustic Grand Piano'))
            melodies.notes = pitch_file
            gen_midi.instruments.append(melodies)
            gen_midi.write(output_dir)
        return pitch_file