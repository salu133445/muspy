"""Event-based representation output interface."""
from math import ceil
from operator import attrgetter, itemgetter
from typing import TYPE_CHECKING, Iterable, List, Tuple

import numpy as np
from bidict import bidict
from numpy import ndarray

if TYPE_CHECKING:
    from ..music import Music


def to_event_representation(
    music: "Music",
    use_single_note_off_event: bool = False,
    use_end_of_sequence_event: bool = False,
    encode_velocity: bool = False,
    force_velocity_event: bool = True,
    max_time_shift: int = 100,
    velocity_bins: int = 32,
    dtype=int,
) -> ndarray:
    """Encode a Music object into event-based representation.

    The event-based represetantion represents music as a sequence of
    events, including note-on, note-off, time-shift and velocity events.
    The output shape is M x 1, where M is the number of events. The
    values encode the events. The default configuration uses 0-127 to
    encode note-on events, 128-255 for note-off events, 256-355 for
    time-shift events, and 356 to 387 for velocity events.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to encode.
    use_single_note_off_event : bool, default: False
        Whether to use a single note-off event for all the pitches. If
        True, the note-off event will close all active notes, which can
        lead to lossy conversion for polyphonic music.
    use_end_of_sequence_event : bool, default: False
        Whether to append an end-of-sequence event to the encoded
        sequence.
    encode_velocity : bool, default: False
        Whether to encode velocities.
    force_velocity_event : bool, default: True
        Whether to add a velocity event before every note-on event. If
        False, velocity events are only used when the note velocity is
        changed (i.e., different from the previous one).
    max_time_shift : int, default: 100
        Maximum time shift (in ticks) to be encoded as an separate
        event. Time shifts larger than `max_time_shift` will be
        decomposed into two or more time-shift events.
    velocity_bins : int, default: 32
        Number of velocity bins to use.
    dtype : np.dtype, type or str, default: int
        Data type of the return array.

    Returns
    -------
    ndarray, shape=(?, 1)
        Encoded array in event-based representation.

    """
    if dtype is None:
        dtype = int

    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes and not use_end_of_sequence_event:
        raise RuntimeError("No notes found.")

    # Sort the notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Compute offsets
    offset_note_on = 0
    offset_note_off = 128
    offset_time_shift = 129 if use_single_note_off_event else 256
    offset_velocity = offset_time_shift + max_time_shift
    if use_end_of_sequence_event:
        offset_eos = offset_velocity + velocity_bins

    # Collect note-related events
    note_events = []
    last_velocity = -1
    for note in notes:
        # Velocity event
        if encode_velocity:
            quantized_velocity = int(note.velocity * velocity_bins / 128)
            if force_velocity_event or quantized_velocity != last_velocity:
                note_events.append(
                    (note.time, offset_velocity + quantized_velocity)
                )
            last_velocity = quantized_velocity
        # Note on event
        note_events.append((note.time, offset_note_on + note.pitch))
        # Note off event
        if use_single_note_off_event:
            note_events.append((note.end, offset_note_off))
        else:
            note_events.append((note.end, offset_note_off + note.pitch))

    # Sort events by time
    note_events.sort(key=itemgetter(0))

    # Create a list for all events
    events = []
    # Initialize the time cursor
    time_cursor = 0
    # Iterate over note events
    for time, code in note_events:
        # If event time is after the time cursor, append tick shift
        # events
        if time > time_cursor:
            div, mod = divmod(time - time_cursor, max_time_shift)
            for _ in range(div):
                events.append(offset_time_shift + max_time_shift - 1)
            if mod > 0:
                events.append(offset_time_shift + mod - 1)
            events.append(code)
            time_cursor = time
        else:
            events.append(code)
    # Append the end-of-sequence event
    if use_end_of_sequence_event:
        events.append(offset_eos)

    return np.array(events, dtype=dtype).reshape(-1, 1)


class EventSequence:
    """A class for handling an event sequence.

    This class serves as a containter for an event sequence. The
    elements are stored as integer codes, where the corresponding events
    are defined by the `indexer` attribute. The event sequence can also
    be accessed as a list of strings by calling `events`.

    Attributes
    ----------
    codes : list of int
        List of event codes.
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    """

    def __init__(
        self, codes: List[int] = None, indexer: bidict[str, int] = None
    ):
        self.codes = codes if codes is not None else []
        self.indexer = indexer if indexer is not None else bidict()

    def __len__(self) -> int:
        return len(self.codes)

    def __repr__(self) -> str:
        return f"EventSequence({repr(self.codes)})"

    def __getitem__(self, key: int) -> int:
        return self.codes[key]

    def __setitem__(self, key: int, value: int):
        self.codes[key] = value

    def __delitem__(self, key: int):
        del self.codes[key]

    def __eq__(self, other) -> bool:
        if isinstance(other, EventSequence):
            return self.codes == other.codes
        return self.codes == other

    @property
    def events(self) -> List[str]:
        """Return a list of all events as strings."""
        return [self.indexer.inverse[elem] for elem in self.codes]

    def get_event(self, idx: int) -> str:
        """Return the event string at a given index."""
        return self.indexer.inverse[self.codes[idx]]

    def to_event(self, code: int) -> str:
        """Return an event code as its corresponding event string.

        This is equivalent to `self.indexer.inverse[code]`.

        """
        return self.indexer.inverse[code]

    def to_code(self, event: str) -> int:
        """Return an event code as its corresponding event string.

        This is equivalent to `self.indexer[event]`.

        """
        return self.indexer[event]

    def append(self, code: int):
        """Append an event code to the event sequence."""
        self.codes.append(code)

    def extend(self, codes: Iterable[int]):
        """Append an event code to the event sequence."""
        self.codes.extend(codes)

    def append_event(self, event: str):
        """Append an event string to the event sequence."""
        self.codes.append(self.to_code(event))

    def extend_events(self, events: List[str]):
        """Extend the event sequence by a list of events."""
        self.codes.extend(self.indexer[event] for event in events)


def get_default_indexer() -> bidict[str, int]:
    """Return the default indexer."""
    indexer = {}
    idx = 0
    # Note-on events
    for i in range(128):
        indexer[f"note_on_{i}"] = idx
        idx += 1
    # Note-off events
    for i in range(128):
        indexer[f"note_off_{i}"] = idx
        idx += 1
    # Time-shift events
    for i in range(1, 101):
        indexer[f"time_shift_{i}"] = idx
        idx += 1
    return bidict(indexer)


class DefaultEventSequence(EventSequence):
    """A class for handling a MIDI-like event sequence.

    Attributes
    ----------
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    """

    def __init__(self, codes: List[int] = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(codes, indexer)
        else:
            super().__init__(codes, get_default_indexer())

    @classmethod
    def to_note_on_event(cls, pitch) -> str:
        """Return a note-on event for a given pitch."""
        return f"note_on_{pitch}"

    @classmethod
    def to_note_off_event(cls, pitch) -> str:
        """Return a note-off event for a given pitch."""
        return f"note_off_{pitch}"

    @classmethod
    def to_time_shift_events(cls, time_shift) -> List[str]:
        """Return a list of time-shift events for a given time-shift."""
        if time_shift <= 100:
            return [f"time_shift_{time_shift}"]
        events = []
        div, mod = divmod(time_shift, 100)
        for _ in range(div):
            events.append("time_shift_100")
        if mod > 0:
            events.append(f"time_shift_{mod}")
        return events


def to_default_event_sequence(
    music: "Music", resolution: int = None
) -> DefaultEventSequence:
    """Return a Music object as a DefaultEventSequence object."""
    # Adjust resolution
    if resolution is not None:
        music.adjust_resolution(resolution)

    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Create a DefaultEventSequence object
    seq = DefaultEventSequence()

    # Collect events
    events = []
    for note in notes:
        events.append((note.time, seq.to_note_on_event(note.pitch)))
        events.append((note.end, seq.to_note_off_event(note.pitch)))

    # Sort the events by time
    events.sort(key=itemgetter(0))

    # Create event sequence
    last_event_time = 0
    for event in events:
        if event[0] > last_event_time:
            time_shift = event[0] - last_event_time
            seq.extend_events(seq.to_time_shift_events(time_shift))
        seq.append_event(event[1])
        last_event_time = event[0]

    return seq


def to_default_event_representation(music: "Music", dtype=int) -> ndarray:
    """Encode a Music object into the default event representation."""
    seq = to_default_event_sequence(music)
    return np.array(seq, dtype=dtype)


def get_performance_indexer() -> bidict[str, int]:
    """Return the default indexer."""
    indexer = {}
    idx = 0
    # Note-on events
    for i in range(128):
        indexer[f"note_on_{i}"] = idx
        idx += 1
    # Note-off events
    for i in range(128):
        indexer[f"note_off_{i}"] = idx
        idx += 1
    # Time-shift events
    for i in range(1, 101):
        indexer[f"time_shift_{i}"] = idx
        idx += 1
    # Velocity events
    for i in range(32):
        indexer[f"velocity_{i}"] = idx
        idx += 1
    return bidict(indexer)


class PerformanceEventSequence(EventSequence):
    """A class for handling a MIDI-like event sequence.

    Attributes
    ----------
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    """

    def __init__(self, codes: List[int] = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(codes, indexer)
        else:
            super().__init__(codes, get_performance_indexer())

    @classmethod
    def to_note_on_event(cls, pitch) -> str:
        """Return a note-on event for a given pitch."""
        return f"note_on_{pitch}"

    @classmethod
    def to_note_off_event(cls, pitch) -> str:
        """Return a note-off event for a given pitch."""
        return f"note_off_{pitch}"

    @classmethod
    def to_velocity_event(cls, velocity) -> str:
        """Return a velocity event for a given velocity."""
        return f"velocity_{velocity//4}"

    @classmethod
    def to_time_shift_events(cls, time_shift) -> List[str]:
        """Return a list of time-shift events for a given time-shift."""
        if time_shift <= 100:
            return [f"time_shift_{time_shift}"]
        events = []
        div, mod = divmod(time_shift, 100)
        for _ in range(div):
            events.append("time_shift_100")
        if mod > 0:
            events.append(f"time_shift_{mod}")
        return events


def to_performance_event_sequence(
    music: "Music", resolution: int = None
) -> PerformanceEventSequence:
    """Return a Music object as a PerformanceEventSequence object."""
    # Adjust resolution
    if resolution is not None:
        music.adjust_resolution(resolution)

    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Create a PerformanceEventSequence object
    seq = PerformanceEventSequence()

    # Collect events
    events = []
    for note in notes:
        events.append((note.time, seq.to_velocity_event(note.velocity)))
        events.append((note.time, seq.to_note_on_event(note.pitch)))
        events.append((note.end, seq.to_note_off_event(note.pitch)))

    # Sort the events by time
    events.sort(key=itemgetter(0))

    # Create event sequence
    last_event_time = 0
    for event in events:
        if event[0] > last_event_time:
            time_shift = event[0] - last_event_time
            seq.extend_events(seq.to_time_shift_events(time_shift))
        seq.append_event(event[1])
        last_event_time = event[0]

    return seq


def to_performance_event_representation(music: "Music", dtype=int) -> ndarray:
    """Encode a Music object to the performance event representation."""
    seq = to_performance_event_sequence(music)
    return np.array(seq, dtype=dtype)


def get_remi_indexer() -> bidict[str, int]:
    """Return the REMI indexer."""
    indexer = {}
    idx = 0
    # Note-on events
    for i in range(128):
        indexer[f"note_on_{i}"] = idx
        idx += 1
    # Note-duration events
    for i in range(1, 65):
        indexer[f"note_duration_{i}"] = idx
        idx += 1
    # Note-velocity events
    for i in range(32):
        indexer[f"note_velocity_{i}"] = idx
        idx += 1
    # Position events
    for i in range(16):
        indexer[f"position_{i}"] = idx
        idx += 1
    # Beat event
    indexer["bar"] = idx
    idx += 1
    # Tempo events
    for i in range(30, 210):
        indexer[f"tempo_{i}"] = idx
        idx += 1
    return bidict(indexer)


class REMIEventSequence(EventSequence):
    """A class for handling the REMI event sequence [1].

    This by default will adjust the resolution to 16.

    Attributes
    ----------
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    Warnings
    --------
    Chord events are not supported.

    References
    ----------
    1. Yu-Siang Huang and Yi-Hsuan Yang, “Pop Music Transformer:
       Beat-based Modeling and Generation of Expressive Pop Piano
       Compositions,” in The 28th ACM International Conference on
       Multimedia (MMR), 2020.

    """

    def __init__(self, codes: List[int] = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(codes, indexer)
        else:
            super().__init__(codes, get_remi_indexer())

    @classmethod
    def to_note_on_event(cls, pitch) -> str:
        """Return a note-on event for a given pitch."""
        return f"note_on_{pitch}"

    @classmethod
    def to_note_duration_event(cls, duration) -> str:
        """Return a note-duration event for a given duration."""
        return f"note_duration_{duration}"

    @classmethod
    def to_note_velocity_event(cls, velocity) -> str:
        """Return a note-velocity event for a given velocity."""
        return f"note_velocity_{velocity // 4}"

    @classmethod
    def to_position_event(cls, position) -> str:
        """Return a position event for a given position."""
        return f"position_{position}"

    @classmethod
    def to_bar_event(cls) -> str:
        """Return a bar event."""
        return "bar"

    @classmethod
    def to_tempo_event(cls, tempo) -> str:
        """Return a position event for a given position."""
        return f"tempo_{int(tempo)}"


def to_remi_event_sequence(music: "Music") -> REMIEventSequence:
    """Return a Music object as a REMIEventSequence object."""
    # Adjust resolution
    music.adjust_resolution(16)

    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Create a REMIEventSequence object
    seq = REMIEventSequence()

    # Collect measure times
    barline_times = [barline.time for barline in music.barlines]
    if barline_times[0] != 0:
        barline_times.insert(0, 0)
    measure_times = np.sort(barline_times)
    assert len(measure_times) > 1

    def _get_measure_position(time) -> Tuple[int, int]:
        measure_idx = np.searchsorted(measure_times, time, "right") - 1
        if measure_idx < len(measure_times) - 1:
            measure_length = (
                measure_times[measure_idx + 1] - measure_times[measure_idx]
            )
        else:
            measure_length = (
                measure_times[measure_idx] - measure_times[measure_idx - 1]
            )
        position = ceil(
            16 * (time - measure_times[measure_idx]) / measure_length
        )
        return measure_idx, position

    # Collect events
    events: List[Tuple[Tuple[int, int], List[str]]] = []
    for barline_time in barline_times:
        events.append(
            (_get_measure_position(barline_time), [seq.to_bar_event()])
        )
    for tempo in music.tempos:
        events.append(
            (
                _get_measure_position(tempo.time),
                [seq.to_tempo_event(tempo.qpm)],
            )
        )
    for note in notes:
        events.append(
            (
                _get_measure_position(note.time),
                [
                    seq.to_note_on_event(note.pitch),
                    seq.to_note_velocity_event(note.velocity),
                    seq.to_note_duration_event(min(note.duration, 32)),
                ],
            )
        )

    # Sort the events by time
    events.sort(key=itemgetter(0))

    # Append the events to the event sequence
    for event in events:
        if event[1][0] != "bar":
            seq.append_event(seq.to_position_event(event[0][1]))
        seq.extend_events(event[1])

    return seq


def to_remi_event_representation(music: "Music", dtype=int) -> ndarray:
    """Encode a Music object into the remi event representation."""
    seq = to_remi_event_sequence(music)
    return np.array(seq, dtype=dtype)


def get_indexer(preset=None) -> bidict:
    """Return a preset indexer."""
    if preset is None or preset.lower() == "midi":
        return get_default_indexer()
    if preset.lower() == "remi":
        return get_remi_indexer()
    if preset.lower() == "performance":
        return get_performance_indexer()
    raise ValueError(f"Unknown preset : {preset}")
