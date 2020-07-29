"""
Metrics
=======

This module provides functions for computing common metrics on a Music
object. This can be useful for analyzing datasets and evaluating
generative models.

"""
from .metrics import (
    drum_in_pattern_rate,
    drum_pattern_consistency,
    empty_beat_rate,
    empty_measure_rate,
    groove_consistency,
    n_pitch_classes_used,
    n_pitches_used,
    pitch_class_entropy,
    pitch_entropy,
    pitch_in_scale_rate,
    pitch_range,
    polyphony,
    polyphony_rate,
    scale_consistency,
)

__all__ = [
    "drum_in_pattern_rate",
    "drum_pattern_consistency",
    "empty_beat_rate",
    "empty_measure_rate",
    "groove_consistency",
    "n_pitch_classes_used",
    "n_pitches_used",
    "pitch_class_entropy",
    "pitch_entropy",
    "pitch_in_scale_rate",
    "pitch_range",
    "polyphony",
    "polyphony_rate",
    "scale_consistency",
]
