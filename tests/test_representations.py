"""Test cases for representations."""
import numpy as np

import muspy

from .utils import TEST_JSON_PATH


def test_note_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_note_representation(music)

    assert encoded.shape == (9, 4)
    assert encoded.dtype == int
    answer = [
        [0, 76, 6, 64],
        [6, 75, 6, 64],
        [12, 76, 6, 64],
        [18, 75, 6, 64],
        [24, 76, 6, 64],
        [30, 71, 6, 64],
        [36, 74, 6, 64],
        [42, 72, 6, 64],
        [48, 69, 6, 64],
    ]
    assert np.all(encoded == np.array(answer, dtype=int))

    # Decoding
    decoded = muspy.from_note_representation(encoded)
    assert decoded[0].notes == music[0].notes


def test_note_representation_start_end():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_note_representation(music, use_start_end=True)

    assert encoded.shape == (9, 4)
    assert encoded.dtype == np.int
    answer = [
        [0, 76, 6, 64],
        [6, 75, 12, 64],
        [12, 76, 18, 64],
        [18, 75, 24, 64],
        [24, 76, 30, 64],
        [30, 71, 36, 64],
        [36, 74, 42, 64],
        [42, 72, 48, 64],
        [48, 69, 54, 64],
    ]
    assert np.all(encoded == np.array(answer, dtype=np.uint8))

    # Decoding
    decoded = muspy.from_note_representation(encoded, use_start_end=True)
    assert decoded[0].notes == music[0].notes


def test_pitch_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_pitch_representation(music)

    assert encoded.shape == (54, 1)

    answer = np.repeat([76, 75, 76, 75, 76, 71, 74, 72, 69], 6)
    assert np.all(encoded.flatten() == answer)

    # Decoding
    decoded = muspy.from_pitch_representation(encoded)
    assert decoded[0].notes == music[0].notes


def test_pitch_representation_hold_state():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_pitch_representation(music, use_hold_state=True)

    assert encoded.shape == (54, 1)

    answer = np.stack(
        [[76, 75, 76, 75, 76, 71, 74, 72, 69]] + [[129] * 9] * 5
    ).T.reshape(-1)
    assert np.all(encoded.flatten() == answer)

    # Decoding
    decoded = muspy.from_pitch_representation(encoded, use_hold_state=True)
    assert decoded[0].notes == music[0].notes


def test_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_event_representation(music, encode_velocity=True)

    assert encoded.shape == (36, 1)

    answer = [
        372,
        76,
        261,
        204,
        372,
        75,
        261,
        203,
        372,
        76,
        261,
        204,
        372,
        75,
        261,
        203,
        372,
        76,
        261,
        204,
        372,
        71,
        261,
        199,
        372,
        74,
        261,
        202,
        372,
        72,
        261,
        200,
        372,
        69,
        261,
        197,
    ]
    assert np.all(encoded.flatten() == np.array(answer))

    # Decoding
    decoded = muspy.from_event_representation(encoded)
    assert decoded[0].notes == music[0].notes


def test_event_representation_single_note_off():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_event_representation(
        music, use_single_note_off_event=True, encode_velocity=True
    )

    assert encoded.shape == (36, 1)

    answer = [
        245,
        76,
        134,
        128,
        245,
        75,
        134,
        128,
        245,
        76,
        134,
        128,
        245,
        75,
        134,
        128,
        245,
        76,
        134,
        128,
        245,
        71,
        134,
        128,
        245,
        74,
        134,
        128,
        245,
        72,
        134,
        128,
        245,
        69,
        134,
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
    encoded = muspy.to_event_representation(
        music, encode_velocity=True, force_velocity_event=False
    )

    assert encoded.shape == (28, 1)

    answer = [
        372,
        76,
        261,
        204,
        75,
        261,
        203,
        76,
        261,
        204,
        75,
        261,
        203,
        76,
        261,
        204,
        71,
        261,
        199,
        74,
        261,
        202,
        72,
        261,
        200,
        69,
        261,
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


def test_default_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    seq = muspy.outputs.event.to_default_event_sequence(music)

    assert len(seq) == 27

    answer = [
        76,
        261,
        204,
        75,
        261,
        203,
        76,
        261,
        204,
        75,
        261,
        203,
        76,
        261,
        204,
        71,
        261,
        199,
        74,
        261,
        202,
        72,
        261,
        200,
        69,
        261,
        197,
    ]
    assert seq == answer

    answer_events = [
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "note_on_75",
        "time_shift_6",
        "note_off_75",
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "note_on_75",
        "time_shift_6",
        "note_off_75",
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "note_on_71",
        "time_shift_6",
        "note_off_71",
        "note_on_74",
        "time_shift_6",
        "note_off_74",
        "note_on_72",
        "time_shift_6",
        "note_off_72",
        "note_on_69",
        "time_shift_6",
        "note_off_69",
    ]
    assert seq.events == answer_events


def test_performance_event_representation():
    music = muspy.load(TEST_JSON_PATH)

    seq = muspy.outputs.event.to_performance_event_sequence(music)

    assert len(seq) == 36

    answer = [
        372,
        76,
        261,
        204,
        372,
        75,
        261,
        203,
        372,
        76,
        261,
        204,
        372,
        75,
        261,
        203,
        372,
        76,
        261,
        204,
        372,
        71,
        261,
        199,
        372,
        74,
        261,
        202,
        372,
        72,
        261,
        200,
        372,
        69,
        261,
        197,
    ]
    assert seq == answer

    answer_events = [
        "velocity_16",
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "velocity_16",
        "note_on_75",
        "time_shift_6",
        "note_off_75",
        "velocity_16",
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "velocity_16",
        "note_on_75",
        "time_shift_6",
        "note_off_75",
        "velocity_16",
        "note_on_76",
        "time_shift_6",
        "note_off_76",
        "velocity_16",
        "note_on_71",
        "time_shift_6",
        "note_off_71",
        "velocity_16",
        "note_on_74",
        "time_shift_6",
        "note_off_74",
        "velocity_16",
        "note_on_72",
        "time_shift_6",
        "note_off_72",
        "velocity_16",
        "note_on_69",
        "time_shift_6",
        "note_off_69",
    ]
    assert seq.events == answer_events


# def test_remi_event_representation():
#     music = muspy.load(TEST_JSON_PATH)

#     seq = muspy.outputs.event.to_remi_event_sequence(music)
#     for event in seq.events:
#         print(event)

#     assert len(seq) == 57

#     answer = [
#         216,
#         192,
#         259,
#         216,
#         192,
#         76,
#         216,
#         198,
#         133,
#         216,
#         198,
#         75,
#         216,
#         192,
#         133,
#         216,
#         192,
#         76,
#         216,
#         198,
#         133,
#         216,
#         198,
#         75,
#         216,
#         192,
#         133,
#         216,
#         192,
#         76,
#         216,
#         198,
#         133,
#         216,
#         198,
#         71,
#         216,
#         192,
#         133,
#         216,
#         192,
#         74,
#         216,
#         198,
#         133,
#         216,
#         198,
#         72,
#         216,
#         192,
#         133,
#         216,
#         192,
#         69,
#         216,
#         198,
#         133,
#     ]
#     assert seq == answer

#     answer_events = [
#         "beat",
#         "position_0",
#         "tempo_72",
#         "beat",
#         "position_0",
#         "note_on_76",
#         "beat",
#         "position_6",
#         "note_duration_6",
#         "beat",
#         "position_6",
#         "note_on_75",
#         "beat",
#         "position_0",
#         "note_duration_6",
#         "beat",
#         "position_0",
#         "note_on_76",
#         "beat",
#         "position_6",
#         "note_duration_6",
#         "beat",
#         "position_6",
#         "note_on_75",
#         "beat",
#         "position_0",
#         "note_duration_6",
#         "beat",
#         "position_0",
#         "note_on_76",
#         "beat",
#         "position_6",
#         "note_duration_6",
#         "beat",
#         "position_6",
#         "note_on_71",
#         "beat",
#         "position_0",
#         "note_duration_6",
#         "beat",
#         "position_0",
#         "note_on_74",
#         "beat",
#         "position_6",
#         "note_duration_6",
#         "beat",
#         "position_12",
#         "note_on_72",
#         "beat",
#         "position_0",
#         "note_duration_6",
#         "beat",
#         "position_0",
#         "note_on_69",
#         "beat",
#         "position_6",
#         "note_duration_6",
#     ]
#     assert seq.events() == answer_events


def test_pianoroll_representation():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_pianoroll_representation(music)

    assert encoded.shape == (55, 128)
    assert encoded.sum() == 6 * 9 * 64

    answer = np.repeat([76, 75, 76, 75, 76, 71, 74, 72, 69], 6)
    assert np.all(encoded.nonzero()[1] == answer)

    # Decoding
    decoded = muspy.from_pianoroll_representation(encoded)
    assert decoded[0].notes == music[0].notes


def test_pianoroll_representation_encode_velocity():
    music = muspy.load(TEST_JSON_PATH)

    # Encoding
    encoded = muspy.to_pianoroll_representation(music, encode_velocity=False)

    assert encoded.shape == (55, 128)
    assert encoded.dtype == np.bool
    assert encoded.sum() == 6 * 9
