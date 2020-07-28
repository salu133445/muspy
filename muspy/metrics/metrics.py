"""Evaluation metrics."""
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
                if count > 127:
                    break
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
                if count > 11:
                    break
    return count


def pitch_range(music: Music) -> int:
    """Return the pitch range."""
    if not music.tracks:
        return 0
    if not any(len(track.notes) > 0 for track in music.tracks):
        return 0

    highest = 0
    lowest = 127
    for track in music.tracks:
        for note in track.notes:
            if note.pitch > highest:
                highest = note.pitch
            if note.pitch < lowest:
                lowest = note.pitch
    return highest - lowest


def empty_beat_rate(music: Music) -> float:
    r"""Return the empty beat rate.

    The empty beat rate is defined as the ratio of the number of empty beats
    (where no pitch is played) to the number of beats. This metric is also
    implemented in Pypianoroll [1].

    .. math:: empty\_beat\_rate = \frac{\#\_of\_empty\_beats}{\#\_of\_beats}

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Empty beat rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, and Yi-Hsuan Yang, “Pypianoroll: Open
       Source Python Package for Handling Multitrack Pianorolls,” in
       Late-Breaking Demos of the 18th International Society for Music
       Information Retrieval Conference (ISMIR), 2018.

    """
    length = max(track.get_end_time() for track in music.tracks)
    total_beats = length // music.resolution
    is_empty = [False] * total_beats
    count = 0
    for track in music.tracks:
        for note in track.notes:
            start = note.start // music.resolution
            end = note.end // music.resolution
            for beat in range(start, end + 1):
                if not is_empty[beat]:
                    is_empty[beat] = True
                    count += 1
    return count / total_beats


def polyphony(music: Music, threshold: int = 2) -> float:
    r"""Return the polyphony measure.

    The polyphony is defined as the ratio of the number of time steps where
    multiple pitches are on to the total number of time steps. Drum tracks
    are ignored. This metric is used in [1].

    .. math::
        polyphony = \frac{
            \#\_of\_time\_steps\_where\_multiple\_pitches\_are\_on
        }{
            \#\_of\_time\_steps
        }

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to evaluate.

    Returns
    -------
    float
        Polyphony.

    References
    ----------
    1. Olof Mogren, "C-RNN-GAN: Continuous recurrent neural networks with
       adversarial training," in NeuIPS Workshop on Constructive Machine
       Learning, 2016.

    """
    length = max(track.get_end_time() for track in music.tracks)
    pianoroll = np.zeros((length, 128), bool)
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            pianoroll[note.start : note.end] = 1
    return (pianoroll.sum(1) > threshold) / len(pianoroll)


def _get_scale(key: int, mode: str) -> ndarray:
    """Return a scale mask for the given key."""
    if mode == "major":
        a_scale_mask = np.array([0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1], bool)
    elif mode == "minor":
        a_scale_mask = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], bool)
    else:
        raise ValueError("`mode` must be either 'major' or 'minor'.")
    return np.roll(a_scale_mask, key)


def in_scale_rate(music: Music, root: int, mode: str) -> float:
    r"""Return the rate of notes in a musical scale.

    In scale rate is defined as the ratio of the number of notes in a scale
    to the total number of notes. Drum tracks are ignored. This metric is
    used in [1].

    .. math::
        in\_scale\_rate = \frac{\#\_of\_notes\_in\_scale}{\#\_of\_notes}

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
        In scale rate.

    References
    ----------
    1. Hao-Wen Dong, Wen-Yi Hsiao, Li-Chia Yang, and Yi-Hsuan Yang,
       "MuseGAN: Multi-track sequential generative adversarial networks for
       symbolic music generation and accompaniment," in Proceedings of the
       32nd AAAI Conference on Artificial Intelligence (AAAI), 2018.

    """
    scale = _get_scale(root, mode.lower())
    count = 0
    in_scale_count = 0
    for track in music.tracks:
        if track.is_drum:
            continue
        for note in track.notes:
            count += 1
            if scale[note.pitch % 12]:
                in_scale_count += 1
    return in_scale_count / count


def scale_consistency(music: Music) -> float:
    r"""Return the largest in scale rate.

    The scale consistency is defined as the largest in scale rate over all
    major and minor scales. Drum tracks are ignored. This metric is used
    in [1].

    .. math::
        scale\_consistency = \max_{root, mode}{in\_scale\_rate(root, mode)}

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
            rate = in_scale_rate(music, root, mode)
            if rate > max_in_scale_rate:
                max_in_scale_rate = rate
    return max_in_scale_rate


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
    prob = counter / counter.sum()
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
    prob = counter / counter.sum()
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
    if measure_resolution % music.resolution > 0:
        raise ValueError(
            "Measure resolution must be a multiple of resolution."
        )

    n_measures = (length // measure_resolution) + 1
    groove_patterns = np.zeros(n_measures, measure_resolution)

    for track in music.tracks:
        for note in track.notes:
            measure, position = divmod(note.start, measure_resolution)
            if not groove_patterns[measure, position]:
                groove_patterns[measure, position] = 1

    hamming_distance = np.count_nonzero(
        groove_patterns[:-1] != groove_patterns[1:]
    )

    return 1 - hamming_distance / (measure_resolution * (n_measures - 1))
