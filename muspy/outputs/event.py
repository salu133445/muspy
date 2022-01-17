"""Event-based representation output interface."""
from operator import attrgetter, itemgetter
from typing import TYPE_CHECKING, Iterable, List

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


class EventSequence(list):
    """A class for handling an event sequence.

    The EventSequence inherits from the builtin list. The elements are
    integer codes of the events defined by its `indexer` attribute. The
    corresponding events can be accessed by calling `events(idx)`.

    Attributes
    ----------
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    """

    def __init__(self, iterable: Iterable = None, indexer: bidict = None):
        if iterable is not None:
            super().__init__(iterable)
        else:
            super().__init__()
        self.indexer = indexer if indexer is not None else bidict()

    def event(self, idx: int) -> str:
        """Return the event at a given index."""
        return self.indexer.inverse[self[idx]]

    def events(self) -> List[str]:
        """Return a list of all events."""
        return [self.indexer.inverse[elem] for elem in self]

    def append_event(self, event: str):
        """Append an event to the event sequence."""
        # pylint: disable=unsubscriptable-object
        self.append(self.indexer[event])

    def extend_events(self, events: List[str]):
        """Extend the event sequence by a list of events."""
        # pylint: disable=unsubscriptable-object
        self.extend(self.indexer[event] for event in events)

    def inverse(self, idx) -> str:
        """Return the corresponding event by its code."""
        return self.indexer.inverse[idx]


def get_default_indexer() -> bidict:
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

    def __init__(self, iterable: Iterable = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(iterable, indexer)
        else:
            super().__init__(iterable, get_default_indexer())

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


def to_default_event_sequence(music: "Music") -> DefaultEventSequence:
    """Return a Music object as a DefaultEventSequence object."""
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


def get_performance_indexer() -> bidict:
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

    def __init__(self, iterable: Iterable = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(iterable, indexer)
        else:
            super().__init__(iterable, get_performance_indexer())

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


def to_performance_event_sequence(music: "Music") -> PerformanceEventSequence:
    """Return a Music object as a PerformanceEventSequence object."""
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


def get_remi_indexer() -> bidict:
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
    # Position events
    for i in range(0, 24):
        indexer[f"position_{i}"] = idx
        idx += 1
    # Beat event
    indexer["beat"] = idx
    idx += 1
    # Tempo events
    for i in range(30, 210):
        indexer[f"tempo_{i}"] = idx
        idx += 1
    return bidict(indexer)


class REMIEventSequence(EventSequence):
    """A class for handling a MIDI-like event sequence.

    Attributes
    ----------
    indexer : bidict, optional
        Indexer that defines the mapping between events and their codes.

    Note
    ----
    Bar events are replaced by beat events. Chord events are currently
    not supported.

    """

    def __init__(self, iterable: Iterable = None, indexer: bidict = None):
        if indexer is not None:
            super().__init__(iterable, indexer)
        else:
            super().__init__(iterable, get_remi_indexer())

    @classmethod
    def to_note_on_event(cls, pitch) -> str:
        """Return a note-on event for a given pitch."""
        return f"note_on_{pitch}"

    @classmethod
    def to_note_duration_event(cls, duration) -> str:
        """Return a note-duration event for a given pitch."""
        return f"note_duration_{duration}"

    @classmethod
    def to_position_event(cls, position) -> str:
        """Return a position event for a given position."""
        return f"position_{position}"

    @classmethod
    def to_beat_event(cls) -> str:
        """Return a beat event."""
        return "beat"

    @classmethod
    def to_tempo_event(cls, tempo) -> str:
        """Return a position event for a given position."""
        return f"tempo_{int(tempo)}"


def to_remi_event_sequence(music: "Music") -> REMIEventSequence:
    """Return a Music object as a REMIEventSequence object."""
    # Collect notes
    notes = []
    for track in music.tracks:
        notes.extend(track.notes)

    # Raise an error if no notes is found
    if not notes:
        raise RuntimeError("No notes found.")

    # Create a REMIEventSequence object
    seq = REMIEventSequence()

    # Collect events
    events = []
    for tempo in music.tempos:
        events.append((tempo.time, seq.to_tempo_event(tempo.qpm)))
    for note in notes:
        events.append((note.time, seq.to_note_on_event(note.pitch)))
        events.append((note.end, seq.to_note_duration_event(note.duration)))

    # Sort the events by time
    events.sort(key=itemgetter(0))

    # Create event sequence
    last_beat = -1
    last_position = -1
    for event in events:
        beat, position = divmod(event[0], music.resolution)
        if beat > last_beat:
            seq.append_event(seq.to_beat_event())
        if position > last_position:
            seq.append_event(
                seq.to_position_event(24 * position // music.resolution)
            )
        seq.append_event(event[1])

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
