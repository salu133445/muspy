"""Test cases for representation processors."""
import numpy as np

import muspy

from .utils import TEST_JSON_PATH


def test_note_representation_processor():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.NoteRepresentationProcessor()

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_note_representation_start_end():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.NoteRepresentationProcessor(use_start_end=True)

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_pitch_representation():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.PitchRepresentationProcessor()

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    assert np.all(encoded.flatten() == np.array(answer, dtype=np.uint8,))

    # Decoding
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_pitch_representation_hold_state():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.PitchRepresentationProcessor(use_hold_state=True)

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.EventRepresentationProcessor()

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_event_representation_force_velocity_event():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.EventRepresentationProcessor(force_velocity_event=False)

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_event_representation_end_of_sequence_event():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.EventRepresentationProcessor(
        use_end_of_sequence_event=True
    )

    # Encoding
    encoded = processor.encode(music[0].notes)

    assert encoded.shape == (37, 1)
    assert encoded.dtype == np.uint16
    assert encoded[-1] == 388

    # Decoding
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_pianoroll_representation():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.PianoRollRepresentationProcessor()

    # Encoding
    encoded = processor.encode(music[0].notes)

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
    decoded = processor.decode(encoded)
    assert decoded == music[0].notes


def test_pianoroll_representation_encode_velocity():
    music = muspy.load(TEST_JSON_PATH)

    processor = muspy.PianoRollRepresentationProcessor(encode_velocity=False)

    # Encoding
    encoded = processor.encode(music[0].notes)

    assert encoded.shape == (19, 128)
    assert encoded.dtype == np.bool
    assert encoded.sum() == 2 * 9
