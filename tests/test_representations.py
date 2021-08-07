"""Test cases for representations."""
import copy

import numpy as np
import pytest

import muspy

from .utils import TEST_JSON_PATH


def test_note_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "note")

    assert encoded.shape == (9, 4)
    assert encoded.dtype == int
    answer = [
        [0, 76, 2, 64],
        [2, 75, 2, 64],
        [4, 76, 2, 64],
        [6, 75, 2, 64],
        [8, 76, 2, 64],
        [10, 71, 2, 64],
        [12, 74, 2, 64],
        [14, 72, 2, 64],
        [16, 69, 2, 64],
    ]
    assert np.all(encoded == np.array(answer, dtype=int))

    # Decoding
    decoded = muspy.from_representation(encoded, "note")
    assert decoded[0].notes == music[0].notes


def test_note_representation_start_end():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "note", use_start_end=True)

    assert encoded.shape == (9, 4)
    assert encoded.dtype == np.int
    answer = [
        [0, 76, 2, 64],
        [2, 75, 4, 64],
        [4, 76, 6, 64],
        [6, 75, 8, 64],
        [8, 76, 10, 64],
        [10, 71, 12, 64],
        [12, 74, 14, 64],
        [14, 72, 16, 64],
        [16, 69, 18, 64],
    ]
    assert np.all(encoded == np.array(answer, dtype=np.uint8,))

    # Decoding
    decoded = muspy.from_representation(encoded, "note", use_start_end=True)
    assert decoded[0].notes == music[0].notes


def test_pitch_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "pitch")

    assert encoded.shape == (18, 1)

    answer = [
        76,
        76,
        75,
        75,
        76,
        76,
        75,
        75,
        76,
        76,
        71,
        71,
        74,
        74,
        72,
        72,
        69,
        69,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_representation(encoded, "pitch")
    assert decoded[0].notes == music[0].notes


def test_pitch_representation_hold_state():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "pitch", use_hold_state=True)

    assert encoded.shape == (18, 1)

    answer = [
        76,
        129,
        75,
        129,
        76,
        129,
        75,
        129,
        76,
        129,
        71,
        129,
        74,
        129,
        72,
        129,
        69,
        129,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_representation(encoded, "pitch", use_hold_state=True)
    assert decoded[0].notes == music[0].notes


def test_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "event", encode_velocity=True)

    assert encoded.shape == (36, 1)

    answer = [
        372,
        76,
        257,
        204,
        372,
        75,
        257,
        203,
        372,
        76,
        257,
        204,
        372,
        75,
        257,
        203,
        372,
        76,
        257,
        204,
        372,
        71,
        257,
        199,
        372,
        74,
        257,
        202,
        372,
        72,
        257,
        200,
        372,
        69,
        257,
        197,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_representation(encoded, "event")
    assert decoded[0].notes == music[0].notes


def test_event_representation_single_note_off():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "event", use_single_note_off_event=True, encode_velocity=True
    )

    assert encoded.shape == (36, 1)

    answer = [
        245,
        76,
        130,
        128,
        245,
        75,
        130,
        128,
        245,
        76,
        130,
        128,
        245,
        75,
        130,
        128,
        245,
        76,
        130,
        128,
        245,
        71,
        130,
        128,
        245,
        74,
        130,
        128,
        245,
        72,
        130,
        128,
        245,
        69,
        130,
        128,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_representation(
        encoded, "event", use_single_note_off_event=True
    )
    assert decoded[0].notes == music[0].notes


def test_event_representation_force_velocity_event():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "event", encode_velocity=True, force_velocity_event=False
    )

    assert encoded.shape == (28, 1)

    answer = [
        372,
        76,
        257,
        204,
        75,
        257,
        203,
        76,
        257,
        204,
        75,
        257,
        203,
        76,
        257,
        204,
        71,
        257,
        199,
        74,
        257,
        202,
        72,
        257,
        200,
        69,
        257,
        197,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_event_representation(encoded, "event")
    assert decoded[0].notes == music[0].notes


def test_event_representation_end_of_sequence_event():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "event", encode_velocity=True, use_end_of_sequence_event=True
    )

    assert encoded.shape == (37, 1)
    assert encoded[-1] == 388

    # Decoding
    decoded = muspy.from_representation(
        encoded, "event", use_end_of_sequence_event=True
    )
    assert decoded[0].notes == music[0].notes


def test_advanced_event_representation_compat():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    processor = muspy.processors.AdvancedEventRepresentationProcessor(
        encode_velocity=True, num_tracks=None,
        resolution=music.resolution)
    encoded = processor.encode(music)

    answer = [
        372,
        76,
        257,
        204,
        372,
        75,
        257,
        203,
        372,
        76,
        257,
        204,
        372,
        75,
        257,
        203,
        372,
        76,
        257,
        204,
        372,
        71,
        257,
        199,
        372,
        74,
        257,
        202,
        372,
        72,
        257,
        200,
        372,
        69,
        257,
        197,
    ]
    assert encoded == answer

    # Decoding
    decoded = processor.decode(encoded)
    assert decoded[0].notes == music[0].notes

@pytest.mark.parametrize("encode_fn", ["encode", "encode_as_tuples", "encode_as_strings"])
def test_advanced_event_representation_multitrack(encode_fn):
    music = muspy.load(TEST_JSON_PATH)

    # Add a new track, transposed and time-shifted
    music.append(copy.deepcopy(music[0]))
    music[1].transpose(-5)
    music[1].adjust_time(lambda t: t + music.resolution)

    music[0].program = 0
    music[1].program = 1
    music[1].is_drum = True

    processor = muspy.processors.AdvancedEventRepresentationProcessor(
        encode_velocity=True, use_end_of_sequence_event=True,
        num_tracks=4, encode_instrument=True,
        resolution=music.resolution)
    decoded = processor.decode(getattr(processor, encode_fn)(music))

    assert len(decoded) == len(music)
    for tr in range(len(music)):
        assert decoded[tr].notes == music[tr].notes
        assert decoded[tr].program == music[tr].program
        assert decoded[tr].is_drum == music[tr].is_drum


def test_pianoroll_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "pianoroll")

    assert encoded.shape == (19, 128)
    assert encoded.sum() == 2 * 9 * 64

    answer = [
        76,
        76,
        75,
        75,
        76,
        76,
        75,
        75,
        76,
        76,
        71,
        71,
        74,
        74,
        72,
        72,
        69,
        69,
    ]
    assert np.all(encoded.nonzero()[1] == np.array(answer))

    # Decoding
    decoded = muspy.from_representation(encoded, "pianoroll")
    assert decoded[0].notes == music[0].notes


def test_pianoroll_representation_encode_velocity():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "pianoroll", encode_velocity=False
    )

    assert encoded.shape == (19, 128)
    assert encoded.dtype == np.bool
    assert encoded.sum() == 2 * 9
