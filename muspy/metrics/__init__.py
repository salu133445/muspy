"""
Metrics
=======

This module provides functions for computing common metrics on a Music
object. This can be useful for analyzing datasets and evaluating
generative models.

"""
from .metrics import (
    chroma_entropy,
    empty_beat_rate,
    groove_consistency,
    in_scale_rate,
    n_chroma_used,
    n_pitches_used,
    pitch_entropy,
    pitch_range,
    polyphony,
    scale_consistency,
)

__all__ = [
    "chroma_entropy",
    "empty_beat_rate",
    "groove_consistency",
    "in_scale_rate",
    "n_chroma_used",
    "n_pitches_used",
    "pitch_entropy",
    "pitch_range",
    "polyphony",
    "scale_consistency",
]
