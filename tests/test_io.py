"""Test cases for `muspy.inputs` and `muspy.outputs` module."""
import os.path
from unittest import TestCase
import shutil
import tempfile

import muspy

DIR = os.path.dirname(__file__)
TEST_JSON_PATH = os.path.join(DIR, "examples", "test.json")
TEST_YAML_PATH = os.path.join(DIR, "examples", "test.yaml")
TEST_MIDI_PATH = os.path.join(DIR, "data", "fur_elise.mid")
TEST_XML_PATH = os.path.join(DIR, "data", "fur_elise.xml")
TEST_MXL_PATH = os.path.join(DIR, "data", "fur_elise.mxl")


class IOTestCase(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)


class JSONIOTestCase(IOTestCase):
    def test_load_save_json(self):
        music = muspy.load(TEST_JSON_PATH)
        music.save(os.path.join(self.test_dir, "test.json"))


class YAMLIOTestCase(IOTestCase):
    def test_load_save_yaml(self):
        music = muspy.load(TEST_YAML_PATH)
        music.save(os.path.join(self.test_dir, "test.yaml"))


class MIDIIOTestCase(IOTestCase):
    def test_read_write_midi(self):
        music = muspy.read_midi(TEST_MIDI_PATH)
        music.write(os.path.join(self.test_dir, "test.mid"))


class MusicXMLIOTestCase(IOTestCase):
    def test_read_musicxml(self):
        music = muspy.read(TEST_XML_PATH)

    def test_read_compressed_musicxml(self):
        music = muspy.read(TEST_MXL_PATH)
