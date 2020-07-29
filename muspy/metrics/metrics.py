"""Evaluation metrics."""
import math

import numpy as np
from numpy import ndarray

from ..music import Music


def n_pitches_used(music: Music) -> int:
    """Return the number of unique pitches used.

    Drum tracks are ignored.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    int
        Number of unique pitch classes used.

    """
    count = 0
    is_used = [False] * 128
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            if not is_used[note.pitch]:
                is_used[note.pitch] = True
                count += 1
    return count


def n_chroma_used(music: Music) -> int:
    """Return the number of unique chroma (pitch classes) used.

    Drum tracks are ignored.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    int
        Number of unique pitch classes used.

    """
    count = 0
    is_used = [False] * 12
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            chroma = note.pitch % 12
            if not is_used[chroma]:
                is_used[chroma] = True
                count += 1
    return count


def pitch_range(music: Music) -> int:
    """Return the pitch range.

    Drum tracks are ignored.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    int
        Pitch range.

    """
    if not music.tracks:
        return 0
    if not any(len(track.notes) > 0 for track in music.tracks):
        return 0

    highest = 0
    lowest = 127
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            if note.pitch > highest:
                highest = note.pitch
            if note.pitch < lowest:
                lowest = note.pitch
    return highest - lowest


def empty_beat_rate(music: Music) -> float:
    r"""Return the ratio of empty beats.

    The empty-beat rate is defined as the ratio of the number of empty beats
    (where no note is played) to the total number of beats. This metric is
    also implemented in Pypianoroll [1].

    .. math:: empty\_beat\_rate = \frac{\#(empty\_beats)}{\#(beats)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Empty-beat rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, and Yi-Hsuan Yang, “Pypianoroll: Open
       Source Python Package for Handling Multitrack Pianorolls,” in
       Late-Breaking Demos of the 18th International Society for Music
       Information Retrieval Conference (ISMIR), 2018.

    """
    length = max(track.get_end_time() for track in music.tracks)
    n_beats = length // music.resolution + 1

    if n_beats < 1:
        return math.nan

    count = 0
    is_empty = [True] * n_beats
    for track in music.tracks:
        for note in track.notes:
            start = note.start // music.resolution
            end = note.end // music.resolution
            for beat in range(start, end + 1):
                if is_empty[beat]:
                    is_empty[beat] = False
                    count += 1
    return 1 - (count / n_beats)


def empty_measure_rate(music: Music, measure_resolution: int) -> float:
    r"""Return the ratio of empty measures.

    The empty-measure rate is defined as the ratio of the number of empty
    measures (where no note is played) to the total number of measures. Note
    that this metric only works for songs with a constant time signature.
    This metric is used in [1].

    .. math:: empty\_measure\_rate = \frac{\#(empty\_measures)}{\#(measures)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.
    measure_resolution : int
        Time steps per measure.

    Returns
    -------
    float
        Empty-measure rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, Li-Chia Yang, and Yi-Hsuan Yang,
       "MuseGAN: Multi-track sequential generative adversarial networks for
       symbolic music generation and accompaniment," in Proceedings of the
       32nd AAAI Conference on Artificial Intelligence (AAAI), 2018.

    """
    length = max(track.get_end_time() for track in music.tracks)
    n_measures = length // measure_resolution + 1

    if n_measures < 1:
        return math.nan

    count = 0
    is_empty = [True] * n_measures
    for track in music.tracks:
        for note in track.notes:
            start = note.start // measure_resolution
            end = note.end // measure_resolution
            for measure in range(start, end + 1):
                if is_empty[measure]:
                    is_empty[measure] = False
                    count += 1
    return 1 - (count / n_measures)


def _get_pianoroll(music: Music) -> ndarray:
    """Return the binary pianoroll matrix."""
    length = max(track.get_end_time() for track in music.tracks)
    pianoroll = np.zeros((length, 128), bool)
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            pianoroll[note.start : note.end, note.pitch] = 1
    return pianoroll


def polyphony(music: Music) -> float:
    r"""Return the average number of pitches being played at the same time.

    The polyphony is defined as the average number of pitches being played
    at the same time, evaluated only at time steps where at least one pitch
    is on. Drum tracks are ignored.

    .. math::
        polyphony = \frac{
            \#(pitches\_at\_time\_steps\_where\_at\_least\_one\_pitch\_is\_on)
        }{
            \#(time\_steps\_where\_at\_least\_one\_pitch\_is\_on)
        }

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Polyphony.

    """
    pianoroll = _get_pianoroll(music)
    denominator = np.count_nonzero(pianoroll.sum(1) > 0)
    if denominator < 1:
        return math.nan
    return pianoroll.sum() / denominator


def polyphony_rate(music: Music, threshold: int = 2) -> float:
    r"""Return the ratio of time steps where multiple pitches are on.

    The polyphony is defined as the ratio of the number of time steps where
    multiple pitches are on to the total number of time steps. Drum tracks
    are ignored. This metric is used in [1], where it is called
    *polyphonicity*.

    .. math::
        polyphony_rate = \frac{
            \#(time\_steps\_where\_multiple\_pitches\_are\_on)
        }{
            \#(time\_steps)
        }

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.
    threshold : int
        The threshold of number of pitches to count into the numerator.

    Returns
    -------
    float
        Polyphony rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, Li-Chia Yang, and Yi-Hsuan Yang,
       "MuseGAN: Multi-track sequential generative adversarial networks for
       symbolic music generation and accompaniment," in Proceedings of the
       32nd AAAI Conference on Artificial Intelligence (AAAI), 2018.

    """
    pianoroll = _get_pianoroll(music)
    if len(pianoroll) < 1:
        return math.nan
    return np.count_nonzero(pianoroll.sum(1) > threshold) / len(pianoroll)


def _get_scale(key: int, mode: str) -> ndarray:
    """Return the scale mask of a specific key."""
    if mode == "major":
        c_scale = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], bool)
    elif mode == "minor":
        c_scale = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0], bool)
    else:
        raise ValueError("`mode` must be either 'major' or 'minor'.")
    return np.roll(c_scale, key)


def pitch_in_scale_rate(music: Music, root: int, mode: str) -> float:
    r"""Return the ratio of pitches in a certain musical scale.

    The pitch-in-scale rate is defined as the ratio of the number of notes
    in a certain scale to the total number of notes. Drum tracks are
    ignored. This metric is used in [1].

    .. math::
        pitch\_in\_scale\_rate = \frac{\#(notes\_in\_scale)}{\#(notes)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.
    root : int
        Root of the scale.
    mode : int
        Mode of the scale.

    Returns
    -------
    float
        Pitch-in-scale rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, Li-Chia Yang, and Yi-Hsuan Yang,
       "MuseGAN: Multi-track sequential generative adversarial networks for
       symbolic music generation and accompaniment," in Proceedings of the
       32nd AAAI Conference on Artificial Intelligence (AAAI), 2018.

    """
    scale = _get_scale(root, mode.lower())
    note_count = 0
    in_scale_count = 0
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            note_count += 1
            if scale[note.pitch % 12]:
                in_scale_count += 1
    if note_count < 1:
        return math.nan
    return in_scale_count / note_count


def scale_consistency(music: Music) -> float:
    r"""Return the largest pitch-in-scale rate.

    The scale consistency is defined as the largest pitch-in-scale rate over
    all major and minor scales. Drum tracks are ignored. This metric is used
    in [1].

    .. math::
        scale\_consistency = \max_{root, mode}{
            pitch\_in\_scale\_rate(root, mode)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Scale consistency.

    References
    ----------
    1. Olof Mogren, "C-RNN-GAN: Continuous recurrent neural networks with
       adversarial training," in NeuIPS Workshop on Constructive Machine
       Learning, 2016.

    """
    max_in_scale_rate = 0.0
    for mode in ("major", "minor"):
        for root in range(12):
            rate = pitch_in_scale_rate(music, root, mode)
            if math.isnan(rate):
                return math.nan
            if rate > max_in_scale_rate:
                max_in_scale_rate = rate
    return max_in_scale_rate


def _get_drum_pattern(res: int, meter: str) -> ndarray:
    """Return the drum pattern mask of a specific meter."""
    drum_pattern = np.zeros(res, dtype=bool)
    drum_pattern[0] = 1
    if meter == "duple":
        if res % 4 == 0:
            drum_pattern[:: (res // 4)] = 1
        if res % 2 == 0:
            drum_pattern[:: (res // 2)] = 1
    elif meter == "triple":
        if res % 3 == 0:
            drum_pattern[:: (res // 3)] = 1
    else:
        raise ValueError("Only duple and triple meters are supported.")
    return drum_pattern


def drum_in_pattern_rate(music: Music, meter: str) -> float:
    r"""Return the ratio of drum notes in a certain drum pattern.

    The drum-in-pattern rate is defined as the ratio of the number of
    notes in a certain scale to the total number of notes. Only drum tracks
    are considered. This metric is used in [1].

    .. math::
        drum\_in\_pattern\_rate = \frac{
            \#(drum\_notes\_in\_pattern)}{\#(drum\_notes)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.
    meter : str, {'duple', 'triple'}
        Meter of the drum pattern.

    Returns
    -------
    float
        Drum-in-pattern rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, Li-Chia Yang, and Yi-Hsuan Yang,
       "MuseGAN: Multi-track sequential generative adversarial networks for
       symbolic music generation and accompaniment," in Proceedings of the
       32nd AAAI Conference on Artificial Intelligence (AAAI), 2018.

    """
    drum_pattern = _get_drum_pattern(music.resolution, meter.lower())
    note_count = 0
    in_pattern_count = 0
    for track in music.tracks:
        if not track.is_drum:
            continue
        for note in track.notes:
            note_count += 1
            if drum_pattern[note.start % music.resolution]:
                in_pattern_count += 1
    if note_count < 1:
        return math.nan
    return in_pattern_count / note_count


def drum_pattern_consistency(music: Music) -> float:
    r"""Return the largest drum-in-pattern rate.

    The drum pattern consistency is defined as the largest drum-in-pattern
    rate over duple and triple meters. Only drum tracks are considered.

    .. math::
        drum\_pattern\_consistency = \max_{meter}{
            drum\_in\_pattern\_rate(meter)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Drum pattern consistency.

    """
    drum_in_duple_pattern_rate = drum_in_pattern_rate(music, "duple")
    if math.isnan(drum_in_duple_pattern_rate):
        return math.nan
    drum_in_triple_pattern_rate = drum_in_pattern_rate(music, "triple")

    if drum_in_duple_pattern_rate > drum_in_triple_pattern_rate:
        return drum_in_duple_pattern_rate
    return drum_in_triple_pattern_rate


def _entropy(prob):
    return -np.nansum(prob * np.log2(prob))


def pitch_entropy(music: Music) -> float:
    r"""Return the entropy of the normalized pitch histogram.

    The pitch entropy is defined as the Shannon entropy of the normalized
    pitch histogram. Drum tracks are ignored. This metric is used in [1].

    .. math::
        pitch\_entropy = -\sum_{i = 0}^{127}{P(pitch=i) \log_2 P(pitch=i)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Pitch entropy.

    See Also
    --------
    :func:`muspy.chroma_entropy`: Compute the entropy of the normalized
      chroma histogram.

    References
    ----------
    1. Shih-Lun Wu and Yi-Hsuan Yang, "The Jazz Transformer on the Front
       Line: Exploring the Shortcomings of AI-composed Music through
       Quantitative Measures”, in Proceedings of the 21st International
       Society for Music Information Retrieval Conference, 2020.

    """
    counter = np.zeros(128)
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            counter[note.pitch] += 1
    denominator = counter.sum()
    if denominator < 1:
        return math.nan
    prob = counter / denominator
    return _entropy(prob)


def chroma_entropy(music: Music) -> float:
    r"""Return the entropy of the normalized chroma (pitch class) histogram.

    The chroma entropy is defined as the Shannon entropy of the normalized
    chroma histogram. Drum tracks are ignored. This metric is used in [1].

    .. math::
        chroma\_entropy = -\sum_{i = 0}^{11}{
            P(chroma=i) \times \log_2 P(chroma=i)}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Chroma entropy.

    See Also
    --------
    :func:`muspy.pitch_entropy`: Compute the entropy of the normalized pitch
      histogram.

    References
    ----------
    1. Shih-Lun Wu and Yi-Hsuan Yang, "The Jazz Transformer on the Front
       Line: Exploring the Shortcomings of AI-composed Music through
       Quantitative Measures”, in Proceedings of the 21st International
       Society for Music Information Retrieval Conference, 2020.

    """
    counter = np.zeros(12)
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            counter[note.pitch % 12] += 1
    denominator = counter.sum()
    if denominator < 1:
        return math.nan
    prob = counter / denominator
    return _entropy(prob)


def groove_consistency(music: Music, measure_resolution: int) -> float:
    r"""Return the groove consistency.

    The groove consistency is defined as the mean hamming distance of the
    neighboring measures.

    .. math::
        groove\_consistency = 1 - \frac{1}{T - 1} \sum_{i = 1}^{T - 1}{
            d(G_i, G_{i + 1})}

    Here, :math:`T` is the number of measures, :math:`G_i` is the binary
    onset vector of the :math:`i`-th measure (a one at position that has an
    onset, otherwise a zero), and :math:`d(G, G')` is the hamming distance
    between two vectors :math:`G` and :math:`G'`. Note that this metric only
    works for songs with a constant time signature. This metric is used in
    [1].

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.
    measure_resolution : int
        Time steps per measure.

    Returns
    -------
    float
        Groove consistency.

    References
    ----------
    1. Shih-Lun Wu and Yi-Hsuan Yang, "The Jazz Transformer on the Front
       Line: Exploring the Shortcomings of AI-composed Music through
       Quantitative Measures”, in Proceedings of the 21st International
       Society for Music Information Retrieval Conference, 2020.

    """
    length = max(track.get_end_time() for track in music.tracks)
    if measure_resolution < 1:
        raise ValueError("Measure resolution must be a positive integer.")

    n_measures = (length // measure_resolution) + 1
    if n_measures < 2:
        return math.nan

    groove_patterns = np.zeros((n_measures, measure_resolution), bool)

    for track in music.tracks:
        for note in track.notes:
            measure, position = divmod(note.start, measure_resolution)
            if not groove_patterns[measure, position]:
                groove_patterns[measure, position] = 1

    hamming_distance = np.count_nonzero(
        groove_patterns[:-1] != groove_patterns[1:]
    )

    return 1 - hamming_distance / (measure_resolution * (n_measures - 1))
