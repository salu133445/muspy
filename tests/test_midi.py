"""Test cases for MIDI I/O."""
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest import TestCase

import numpy as np

import muspy
from muspy import MIDIError, MusicXMLError

DATA_DIR = Path(__file__).parent / "data" / "midi"


class MIDIInputTestCase(TestCase):
    def test_empty(self):
        music = muspy.read(DATA_DIR / "empty.mid")

        self.assertEqual(len(music.tracks), 0)
        self.assertEqual(music.meta.source.format, "midi")

    def test_type2(self):
        with self.assertRaises(MIDIError):
            music = muspy.read(DATA_DIR / "type2.mid")

    def test_resolution(self):
        music = muspy.read(DATA_DIR / "ticks-per-beat-480.mid")

        self.assertEqual(music.resolution, 480)

    def test_zero_ticks_per_beat(self):
        with self.assertRaises(MIDIError):
            music = muspy.read(DATA_DIR / "zero-ticks-per-beat.mid")

    def test_negative_ticks_per_beat(self):
        with self.assertRaises(MIDIError):
            music = muspy.read(DATA_DIR / "negative-ticks-per-beat.mid")

    def test_multiple_copyrights(self):
        music = muspy.read(DATA_DIR / "multiple-copyrights.mid")

        self.assertEqual(
            music.meta.source.copyright,
            "Test copyright. Another test copyright.",
        )

    def test_pitches(self):
        music = muspy.read(DATA_DIR / "pitches.mid")

        self.assertEqual(len(music.tracks), 1)

        notes = music.tracks[0].notes
        self.assertEqual(len(notes), 128)

        for i, note in enumerate(notes):

            self.assertEqual(note.start, music.resolution * i)
            self.assertEqual(note.duration, music.resolution)
            self.assertEqual(note.pitch, i)

    def test_durations(self):
        music = muspy.read(DATA_DIR / "durations.mid")

        self.assertEqual(len(music.tracks), 1)

        notes = music.tracks[0].notes
        self.assertEqual(len(notes), 11)

        # Answers
        durations = [
            16,
            8,
            4,
            2,
            1,
            0.5,
            0.25,
            0.125,
            0.0625,
            0.03125,
            0.03125,
        ]

        for note, duration in zip(notes, durations):
            self.assertEqual(note.duration, music.resolution * duration)

    def test_tempos(self):
        music = muspy.read(DATA_DIR / "tempos.mid")

        self.assertEqual(len(music.tempos), 2)

        self.assertEqual(music.tempos[0].time, 0)
        self.assertEqual(music.tempos[0].tempo, 100)

        self.assertEqual(music.tempos[1].time, 4 * music.resolution)
        self.assertEqual(music.tempos[1].tempo, 120)

    def test_time_signatures(self):
        music = muspy.read(DATA_DIR / "time-signatures.mid")

        self.assertEqual(len(music.time_signatures), 11)

        # Answers
        numerators = [2, 4, 2, 3, 2, 3, 4, 5, 3, 6, 12]
        denominators = [2, 4, 2, 2, 4, 4, 4, 4, 8, 8, 8]
        starts = np.insert(
            np.cumsum(4 * np.array(numerators) / np.array(denominators)), 0, 0
        )

        for i, time_signature in enumerate(music.time_signatures):
            self.assertEqual(
                time_signature.time, int(music.resolution * starts[i])
            )
            self.assertEqual(time_signature.numerator, numerators[i])
            self.assertEqual(time_signature.denominator, denominators[i])

    def test_key_signatures(self):
        music = muspy.read(DATA_DIR / "key-signatures.mid")

        # Answers
        keys = [
            "A",
            "A#m",
            "Ab",
            "Abm",
            "Am",
            "B",
            "Bb",
            "Bbm",
            "Bm",
            "C",
            "C#",
            "C#m",
            "Cb",
            "Cm",
            "D",
            "D#m",
            "Db",
            "Dm",
            "E",
            "Eb",
            "Ebm",
            "Em",
            "F",
            "F#",
            "F#m",
            "Fm",
            "G",
            "G#m",
            "Gb",
            "Gm",
        ]
        is_majors = ["m" not in key for key in keys]
        roots = [key.strip("m") for key in keys]

        for i, key_signature in enumerate(music.key_signatures):
            self.assertEqual(key_signature.time, 4 * music.resolution * i)
            self.assertEqual(key_signature.root, roots[i])
            if is_majors[i]:
                self.assertEqual(key_signature.mode, "major")
            else:
                self.assertEqual(key_signature.mode, "minor")

    def test_chords(self):
        music = muspy.read(DATA_DIR / "chords.mid")

        notes = music.tracks[0].notes
        self.assertEqual(len(notes), 12)

        # Answers
        pitches = [60, 64, 67]

        for i, note in enumerate(notes):
            self.assertEqual(note.start, 2 * music.resolution * (i // 3))
            self.assertEqual(note.duration, music.resolution)
            self.assertEqual(note.pitch, pitches[i % 3])

    def test_single_track_multiple_channels(self):
        music = muspy.read(DATA_DIR / "multichannel.mid")

        self.assertEqual(len(music.tracks), 4)

        # Answers
        pitches = [60, 64, 67, 72]

        for track, pitch in zip(music.tracks, pitches):
            self.assertEqual(track.notes[0].start, 0)
            self.assertEqual(track.notes[0].duration, music.resolution)
            self.assertEqual(track.notes[0].pitch, pitch)

    def test_multitrack(self):
        music = muspy.read(DATA_DIR / "multitrack.mid")

        self.assertEqual(len(music.tracks), 4)

        # Answers
        pitches = [60, 64, 67, 72]

        for i, (track, pitch) in enumerate(zip(music.tracks, pitches)):
            self.assertEqual(track.name, "Track " + str(i))
            self.assertEqual(track.notes[0].start, 0)
            self.assertEqual(track.notes[0].duration, 4 * music.resolution)
            self.assertEqual(track.notes[0].pitch, pitch)


class RealworldMIDIInputTestCase(TestCase):
    def test_realworld(self):
        music = muspy.read(DATA_DIR / "fur-elise.mid")

        self.assertEqual(music.meta.source.filename, "fur-elise.mid")
        self.assertEqual(music.meta.source.format, "midi")

        self.assertEqual(len(music.tracks), 2)

        self.assertEqual(len(music.tempos), 2)
        self.assertEqual(round(music.tempos[0].tempo), 72)
        self.assertEqual(round(music.tempos[1].tempo), 72)

        self.assertEqual(len(music.key_signatures), 2)
        self.assertEqual(music.key_signatures[0].root, "C")
        self.assertEqual(music.key_signatures[0].mode, "major")

        self.assertEqual(len(music.time_signatures), 7)

        numerators = [1, 3, 2, 1, 3, 3, 2]
        for i, time_signature in enumerate(music.time_signatures):
            self.assertEqual(time_signature.numerator, numerators[i])
            self.assertEqual(time_signature.denominator, 8)
