"""
Metrics
=======

This module provides functions for computing common metrics on a Music
object. This can be useful for analyzing datasets and evaluating
generative models.

"""
from .metrics import (
    chroma_entropy,
    drum_in_pattern_rate,
    drum_pattern_consistency,
    empty_measure_rate,
    empty_beat_rate,
    groove_consistency,
    n_chroma_used,
    n_pitches_used,
    pitch_entropy,
    pitch_in_scale_rate,
    pitch_range,
    polyphony,
    polyphony_rate,
    scale_consistency,
)

__all__ = [
    "chroma_entropy",
    "drum_in_pattern_rate",
    "drum_pattern_consistency",
    "empty_beat_rate",
    "empty_measure_rate",
    "groove_consistency",
    "n_chroma_used",
    "n_pitches_used",
    "pitch_entropy",
    "pitch_in_scale_rate",
    "pitch_range",
    "polyphony",
    "polyphony_rate",
    "scale_consistency",
]
