=======
Metrics
=======

MusPy provides several several objective metrics proposed in the literature, summarized as follows.

- **Pitch-related metrics**: pitch_range, n_pitches_used, n_pitch_classes_used, polyphony, polyphony rate, pitch-in-scale rate, scale consistency, pitch entropy and pitch class entropy.
- **Rhythm-related metrics**: empty-beat rate, drum-in-pattern rate, drum pattern consistency and groove consistency.
- **Other metrics**:* empty_measure_rate.

These objective metrics could be used to evaluate a music generation system by comparing the statistical difference between the training data and the generated samples.


Pitch-related metrics
=====================

.. autofunction:: muspy.pitch_range
    :noindex:

.. autofunction:: muspy.n_pitches_used
    :noindex:

.. autofunction:: muspy.n_pitch_classes_used
    :noindex:

.. autofunction:: muspy.polyphony
    :noindex:

.. autofunction:: muspy.polyphony_rate
    :noindex:

.. autofunction:: muspy.pitch_in_scale_rate
    :noindex:

.. autofunction:: muspy.scale_consistency
    :noindex:

.. autofunction:: muspy.pitch_entropy
    :noindex:

.. autofunction:: muspy.pitch_class_entropy
    :noindex:


Rhythm-related metrics
======================

.. autofunction:: muspy.empty_beat_rate
    :noindex:

.. autofunction:: muspy.drum_in_pattern_rate
    :noindex:

.. autofunction:: muspy.drum_pattern_consistency
    :noindex:

.. autofunction:: muspy.groove_consistency
    :noindex:


Other metrics
=============

.. autofunction:: muspy.empty_measure_rate
    :noindex:
