# A processor for midi_event midi processing 
# Thanks for the reference to Yang-KiChang's midi processor
# RSnut 2020.3.15
import pretty_midi as pyd
import numpy as np
import os
import random
# from loader.chordloader import Chord_Loader
import copy

class MidiEventProcessor:
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name
        # 128 for note on
        # 128 for note off
        # 32 for velocity
        # 100 for time shifting
        # max duration interval = 1 / 100 = 10ms
        self.max_dur = 100
        self.max_vocab = 388
        self.start_index = {
            "note_on": 0,
            "note_off": 128,
            "time_shift": 256,
            "velocity": 356
        }
    def encode(self, inst_seq):
        # convert the midi note sequences into midi event seq
        # input: n * Ln x 128 | output: Q x 388  
        # TODO: sustain issue
        notes = []
        events = []
        for inst in inst_seq:
            notes.extend(inst.notes)
        meta_events = []
        notes.sort(key = lambda x: x.start)
        for note in notes:
            token_on = {"name": "note_on", "time": note.start,
                    "pitch":note.pitch,"vel":note.velocity}
            token_off = {"name": "note_off", "time": note.end,
                    "pitch":note.pitch,"vel":None}
            meta_events.extend([token_on,token_off])
        meta_events.sort(key = lambda x: x["time"])
        time_shift = 0.0
        cur_vel = 0.0
        for me in meta_events:
            duration = int(round((me["time"] - time_shift) * 100))
            while(duration >= self.max_dur):
                events.append(self.start_index["time_shift"] + self.max_dur - 1)
                duration -= self.max_dur
            if duration > 0:
                events.append(self.start_index["time_shift"] + duration - 1)
            if me["vel"] is not None:
                if cur_vel != me["vel"]:
                    cur_vel = me["vel"]
                    events.append(self.start_index["velocity"] + (me["vel"] // 4))
            events.append(self.start_index[me["name"]] + me["pitch"])
            time_shift = me["time"]
        return events

    def decode(self, event_seq, output_dir = None):
        # convert the midi_event seq into midi_file, if output_dir is not None, it will output the midi
        # input: Q x 388  | output: L x 128 
        # print(event_sequence)
        time_shift = 0.0
        cur_vel = 0.0
        meta_events = []
        note_on_dict = {}
        notes = []
        for e in event_seq:
            if self.start_index["note_on"] <= e < self.start_index["note_off"]:
                token_on = {"name": "note_on", "time": time_shift,
                    "pitch":e,"vel":cur_vel}
                meta_events.append(token_on)
            if self.start_index["note_off"] <= e < self.start_index["time_shift"]:
                token_off = {"name": "note_off", "time": time_shift,
                    "pitch":e - self.start_index["note_off"],"vel":cur_vel}
                meta_events.append(token_off)
            if self.start_index["time_shift"] <= e < self.start_index["velocity"]:
                time_shift += (e - self.start_index["time_shift"] + 1) / 100
            if self.start_index["velocity"] <= e < self.max_vocab:
                cur_vel = (e - self.start_index["velocity"]) * 4
        skip_notes = []
        for me in meta_events:
            if me["name"] == "note_on":
                note_on_dict[me["pitch"]] = me
            elif me["name"] == "note_off":
                try:
                    token_on = note_on_dict[me["pitch"]]
                    token_off = me
                    if token_on["time"] == token_off["time"]:
                        continue
                    notes.append(pyd.Note(velocity = token_on["vel"], pitch = token_on["pitch"], 
                        start = token_on["time"], end = token_off["time"]))
                except:
                    skip_notes.append(me)
        notes.sort(key=lambda x:x.start)
        if output_dir is not None:
            gen_midi = pyd.PrettyMIDI()
            melodies = pyd.Instrument(program = pyd.instrument_name_to_program('Acoustic Grand Piano'))
            melodies.notes = notes
            gen_midi.instruments.append(melodies)
            gen_midi.write(output_dir)
        return notes,skip_notes