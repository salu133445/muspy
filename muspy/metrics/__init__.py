"""
Metrics
=======

This module provides functions for computing common metrics on a Music
object. This can be useful for analyzing datasets and evaluating
generative models.

"""
from .basic import PPL, BLEU

__all__ = [
    "PPL",
    "BLEU"
]
