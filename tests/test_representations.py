"""Test cases for representations."""
import numpy as np

import muspy

from .utils import TEST_JSON_PATH


def test_note_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "note")

    assert encoded.shape == (9, 4)
    assert encoded.dtype == np.uint8
    answer = [
        [76, 0, 2, 64],
        [75, 2, 2, 64],
        [76, 4, 2, 64],
        [75, 6, 2, 64],
        [76, 8, 2, 64],
        [71, 10, 2, 64],
        [74, 12, 2, 64],
        [72, 14, 2, 64],
        [69, 16, 2, 64],
    ]
    assert np.all(encoded == np.array(answer, dtype=np.uint8))

    # Decoding
    decoded = muspy.from_representation(encoded, "note")
    assert decoded[0].notes == music[0].notes


def test_note_representation_start_end():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "note", use_start_end=True)

    assert encoded.shape == (9, 4)
    assert encoded.dtype == np.uint8
    answer = [
        [76, 0, 2, 64],
        [75, 2, 4, 64],
        [76, 4, 6, 64],
        [75, 6, 8, 64],
        [76, 8, 10, 64],
        [71, 10, 12, 64],
        [74, 12, 14, 64],
        [72, 14, 16, 64],
        [69, 16, 18, 64],
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
    assert encoded.dtype == np.uint8

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
    assert np.all(encoded.flatten() == np.array(answer, dtype=np.uint8))

    # Decoding
    decoded = muspy.from_representation(encoded, "pitch")
    assert decoded[0].notes == music[0].notes


def test_pitch_representation_hold_state():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "pitch", use_hold_state=True)

    assert encoded.shape == (18, 1)
    assert encoded.dtype == np.uint8

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
    assert np.all(encoded.flatten() == np.array(answer, dtype=np.uint8))

    # Decoding
    decoded = muspy.from_representation(encoded, "pitch", use_hold_state=True)
    assert decoded[0].notes == music[0].notes


def test_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "event")

    assert encoded.shape == (36, 1)
    assert encoded.dtype == np.uint16

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
    assert np.all(encoded.flatten() == np.array(answer, dtype=np.uint16))

    # Decoding
    decoded = muspy.from_representation(encoded, "event")
    assert decoded[0].notes == music[0].notes


def test_event_representation_force_velocity_event():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "event", force_velocity_event=False
    )

    assert encoded.shape == (28, 1)
    assert encoded.dtype == np.uint16

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
    assert np.all(encoded.flatten() == np.array(answer, dtype=np.uint16))

    # Decoding
    decoded = muspy.from_event_representation(encoded, "event")
    assert decoded[0].notes == music[0].notes


def test_event_representation_end_of_sequence_event():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(
        music, "event", use_end_of_sequence_event=True
    )

    assert encoded.shape == (37, 1)
    assert encoded.dtype == np.uint16
    assert encoded[-1] == 388

    # Decoding
    decoded = muspy.from_representation(
        encoded, "event", use_end_of_sequence_event=True
    )
    assert decoded[0].notes == music[0].notes


def test_pianoroll_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_representation(music, "pianoroll")

    assert encoded.shape == (19, 128)
    assert encoded.dtype == np.uint8
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
    assert np.all(encoded.nonzero()[1] == np.array(answer, dtype=np.uint8))

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
