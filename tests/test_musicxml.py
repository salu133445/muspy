"""Test cases for `muspy.inputs` and `muspy.outputs` module."""
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

import muspy

DATA_DIR = Path(__file__).parent / "data" / "musicxml"


class OutputTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)


class MusicXMLTestCase(TestCase):
    def test_read_musicxml(self):
        music = muspy.read(DATA_DIR / "01a-Pitches-Pitches.xml")

        # Basic tests
        assert music.resolution == 1

        assert len(music.tracks) == 1
        assert len(music.key_signatures) == 1
        assert len(music.time_signatures) == 1

        assert music.key_signatures[0].time == 0
        assert music.key_signatures[0].root == "C"
        assert music.key_signatures[0].time == "major"

        assert music.time_signatures[0].time == 0
        assert music.time_signatures[0].numerator == 4
        assert music.time_signatures[0].denominator == 4

        assert music.source.filename == "01a-Pitches-Pitches.xml"
        assert music.source.format == "musicxml"

        assert len(music.tracks[0].notes == 102)
