"""Test cases for audio output interface."""
import numpy as np
import scipy.io.wavfile

import muspy

from .utils import TEST_JSON_PATH


def test_synthesis():
    muspy.download_musescore_soundfont()
    music = muspy.load(TEST_JSON_PATH)
    waveform = muspy.synthesize(music)

    assert waveform.shape[1] == 2
    assert abs(len(waveform) - 1.875 * 44100) < 1000
    assert abs(np.abs(waveform).max() - 3500) < 500


def test_synthesis_options():
    muspy.download_musescore_soundfont()
    music = muspy.load(TEST_JSON_PATH)
    waveform = muspy.synthesize(
        music, gain=2, options="-o synth.polyphony=512"
    )

    assert waveform.shape[1] == 2
    assert abs(len(waveform) - 1.875 * 44100) < 1000
    assert abs(np.abs(waveform).max() - 7000) < 500


def test_write_audio(tmp_path):
    muspy.download_musescore_soundfont()
    music = muspy.load(TEST_JSON_PATH)
    music.write_audio(tmp_path / "test.wav")
    rate, waveform = scipy.io.wavfile.read(tmp_path / "test.wav")

    assert rate == 44100
    assert waveform.shape[1] == 2
    assert abs(len(waveform) - 1.875 * 44100) < 1000
    assert abs(np.abs(waveform).max() - 3500) < 500
