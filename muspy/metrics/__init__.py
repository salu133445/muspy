"""
Metrics
=======

This module provides functions for computing common metrics on a Music
object. This can be useful for analyzing datasets and evaluating
generative models.

"""
from .metrics import (
    empty_beat_rate,
    in_scale_rate,
    n_pitch_classes_used,
    n_pitches_used,
    pitch_range,
    polyphony,
)

__all__ = [
    "empty_beat_rate",
    "in_scale_rate",
    "n_pitch_classes_used",
    "n_pitches_used",
    "pitch_range",
    "polyphony",
]
