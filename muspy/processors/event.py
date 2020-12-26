from collections import defaultdict, deque
from operator import attrgetter, itemgetter
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, DefaultDict, List
import warnings

from bidict import frozenbidict
import numpy as np
from numpy import ndarray

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


__all__ = [
    "EventRepresentationProcessor",
]


# Event constants
NOTE_ON = "note_on"        # note_on(track_id, pitch)
NOTE_OFF = "note_off"      # note_off(track_id, pitch)
VELOCITY = "velocity"      # velocity(track_id, velocity)
PROGRAM = "program"        # program(track_id, program)
DRUM = "drum"              # drum(track_id)
TIME_SHIFT = "time_shift"  # time_shift(ticks)
EOS = "eos"                # eos()

ALL_NOTES = -1


class EventRepresentationProcessor:
    """Event-based representation processor.
    The event-based represetantion represents music as a sequence of
    events, including note-on, note-off, time-shift and velocity events.
    The output shape is M x 1, where M is the number of events. The
    values encode the events. The default configuration uses 0-127 to
    encode note-one events, 128-255 for note-off events, 256-355 for
    time-shift events, and 356 to 387 for velocity events.
    Attributes
    ----------
    use_single_note_off_event : bool
        Whether to use a single note-off event for all the pitches. If
        True, the note-off event will close all active notes, which can
        lead to lossy conversion for polyphonic music. Defaults to
        False.
    use_end_of_sequence_event : bool
        Whether to append an end-of-sequence event to the encoded
        sequence. Defaults to False.
    encode_velocity : bool
        Whether to encode velocities.
    force_velocity_event : bool
        Whether to add a velocity event before every note-on event. If
        False, velocity events are only used when the note velocity is
        changed (i.e., different from the previous one). Defaults to
        True.
    max_time_shift : int
        Maximum time shift (in ticks) to be encoded as an separate
        event. Time shifts larger than `max_time_shift` will be
        decomposed into two or more time-shift events. Defaults to 100.
    velocity_bins : int
        Number of velocity bins to use. Defaults to 32.
    default_velocity : int
        Default velocity value to use when decoding. Defaults to 64.
    encode_instrument: bool
        Whether to encode the `program` and `is_drum` attributes for
        each track. Defaults to False.
    default_program: int
        Default `program` value to use when decoding. Defaults to 0.
    default_is_drum: bool
        Default `is_drum` value to use when decoding. Defaults to
        False.
    resolution: int
        Time steps per quarter note to use when decoding. Defaults to
        `muspy.DEFAULT_RESOLUTION`.
    num_tracks: int or None
        The maximum number of tracks. Defaults to None, which means
        single-track mode (encode all events as if they were in one
        track).
    ignore_empty_tracks: bool
        Whether empty tracks should be ignored when encoding and deleted
        when decoding. Defaults to False.
    duplicate_note_mode : {'fifo', 'lifo', 'close_all'}
        Policy for dealing with duplicate notes. When a note off event
        is presetned while there are multiple correspoding note on
        events that have not yet been closed, we need a policy to decide
        which note on messages to close. This is only effective when
        `use_single_note_off_event` is False. Defaults to 'fifo'.
        - 'fifo' (first in first out): close the earliest note on
        - 'lifo' (first in first out): close the latest note on
        - 'close_all': close all note on messages
    """

    def __init__(
        self,
        use_single_note_off_event: bool = False,
        use_end_of_sequence_event: bool = False,
        encode_velocity: bool = False,
        force_velocity_event: bool = True,
        max_time_shift: int = 100,
        velocity_bins: int = 32,
        default_velocity: int = 64,
        encode_instrument: bool = False,
        default_program: int = 0,
        default_is_drum: bool = False,
        num_tracks: Optional[int] = None,
        ignore_empty_tracks: bool = False,
        resolution: int = DEFAULT_RESOLUTION,
        duplicate_note_mode: str = "fifo",
    ):
        self.use_single_note_off_event = use_single_note_off_event
        self.use_end_of_sequence_event = use_end_of_sequence_event
        self.encode_velocity = encode_velocity
        self.force_velocity_event = force_velocity_event
        self.max_time_shift = max_time_shift
        self.velocity_bins = velocity_bins
        self.default_velocity = default_velocity
        self.encode_instrument = encode_instrument
        self.default_program = default_program
        self.default_is_drum = default_is_drum
        self.num_tracks = num_tracks
        self.ignore_empty_tracks = ignore_empty_tracks
        self.resolution = resolution
        self.duplicate_note_mode = duplicate_note_mode

        if encode_instrument and num_tracks is None:
            raise ValueError(
                'Cannot encode instruments when num_tracks is None')

        # Create vocabulary of events
        vocab_list = []  # type: list
        track_ids = [0] if num_tracks is None else range(num_tracks)
        vocab_list.extend(
            (NOTE_ON, tr, i)
            for tr in track_ids
            for i in range(128))
        vocab_list.extend(
            (NOTE_OFF, tr, i)
            for tr in track_ids
            for i in (
                [ALL_NOTES] if use_single_note_off_event else range(128)))
        vocab_list.extend(
            (TIME_SHIFT, t) for t in range(1, max_time_shift + 1))
        if encode_velocity or num_tracks is None:
            # In single-track mode, always include velocity tokens
            # for backwards compatibility
            vocab_list.extend(
                (VELOCITY, tr, v)
                for tr in track_ids
                for v in range(velocity_bins))
        if encode_instrument:
            vocab_list.extend((PROGRAM, tr, pr)
                              for tr in track_ids
                              for pr in range(128))
            vocab_list.extend((DRUM, tr) for tr in track_ids)
        if use_end_of_sequence_event:
            vocab_list.append((EOS,))

        # Map human-readable tuples to integers
        self.vocab = frozenbidict(
            enumerate(vocab_list)).inverse  # type: frozenbidict[Any, int]

    def encode(self, music: Music) -> ndarray:
        if music.resolution != self.resolution:
            warnings.warn(
                'Expected a resolution of {} TPQN, got {}'.format(
                    self.resolution, music.resolution),
                RuntimeWarning)

        # Create a list for all events
        events = []  # type: List[tuple]

        # Collect notes by track
        if self.num_tracks is None:
            # Put all notes in one track
            tracks = [[n for track in music.tracks for n in track.notes]]
        else:
            # Keep only num_tracks non-empty tracks
            # TODO: Maybe warn or throw exception if too many tracks
            track_objs = music.tracks
            if self.ignore_empty_tracks:
                track_objs = [track for track in track_objs if track.notes]
            track_objs = track_objs[:self.num_tracks]

            tracks = [[n for n in track.notes] for track in track_objs]

            # Create instrument events for all tracks
            if self.encode_instrument:
                for track_id, track in enumerate(track_objs):
                    if track.is_drum:
                        events.append((DRUM, track_id))
                    events.append((PROGRAM, track_id, track.program))

        # Flatten, store track index with each note
        notes = [(n, tr) for tr, notes in enumerate(tracks) for n in notes]

        # Raise an error if no notes is found
        if not notes and not self.use_end_of_sequence_event:
            raise RuntimeError("No notes found.")

        # Sort the notes
        note_key_fn = attrgetter("time", "pitch", "duration", "velocity")
        notes.sort(key=lambda n_tr: (note_key_fn(n_tr[0]), n_tr[1]))

        # Collect note-related events
        note_events = []
        last_velocity = {tr: -1 for tr in range(len(tracks))}
        for note, track_id in notes:
            # Velocity event
            if self.encode_velocity:
                quant_velocity = int(note.velocity * self.velocity_bins / 128)
                if (self.force_velocity_event
                        or quant_velocity != last_velocity[track_id]):
                    note_events.append(
                        (note.time, (VELOCITY, track_id, quant_velocity))
                    )
                last_velocity[track_id] = quant_velocity
            # Note on event
            note_events.append((note.time, (NOTE_ON, track_id, note.pitch)))
            # Note off event
            if self.use_single_note_off_event:
                note_events.append((note.end, (NOTE_OFF, track_id, ALL_NOTES)))
            else:
                note_events.append(
                    (note.end, (NOTE_OFF, track_id, note.pitch)))

        # Sort events by time
        note_events.sort(key=itemgetter(0))

        # Initialize the time cursor
        time_cursor = 0
        # Iterate over note events
        for time, event in note_events:
            # If event time is after the time cursor, append tick shift
            # events
            if time > time_cursor:
                div, mod = divmod(time - time_cursor, self.max_time_shift)
                for _ in range(div):
                    events.append((TIME_SHIFT, self.max_time_shift))
                if mod > 0:
                    events.append((TIME_SHIFT, mod))
                events.append(event)
                time_cursor = time
            else:
                events.append(event)
        # Append the end-of-sequence event
        if self.use_end_of_sequence_event:
            events.append((EOS,))

        ids = [self.vocab[e] for e in events]
        return np.array(ids, np.uint16).reshape(-1, 1)

    def decode(self, array: ndarray) -> Music:
        """Decode event-based representation into a Music object.
        Parameters
        ----------
        array : ndarray
            Array in event-based representation to decode. Cast to
            integer if not of integer type.
        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.
        See Also
        --------
        :func:`muspy.from_event_representation` :
            Return a Music object converted from event-based
            representation.
        """
        # Cast the array to integer
        if not np.issubdtype(array.dtype, np.integer):
            array = array.astype(np.int)

        # Convert integers to events, skip unknown
        vocab_inv = self.vocab.inverse
        events = [vocab_inv[e] for e in array.flat if e in vocab_inv]

        # Decode events, keeping track of information for each track
        time = 0  # Time is common for all tracks
        curr_velocity = defaultdict(
            lambda: self.default_velocity)  # type: DefaultDict[int, int]
        velocity_factor = 128 / self.velocity_bins
        tracks = defaultdict(lambda: Track(
            program=self.default_program,
            is_drum=self.default_is_drum))  # type: DefaultDict[int, Track]
        program_is_set = defaultdict(bool)  # type: DefaultDict[int, bool]

        # Keep track of active note on messages for each track
        active_notes = defaultdict(lambda: defaultdict(deque)) \
            # type: DefaultDict[int, DefaultDict[int, deque]]

        # Iterate over the events
        for (event, *args) in events:
            if event == EOS:
                break

            if event == NOTE_ON:
                track_id, pitch = args
                active_notes[track_id][pitch].append(
                    Note(
                        time=time,
                        pitch=pitch,
                        velocity=curr_velocity[track_id],
                        duration=-1
                    )
                )

            elif event == NOTE_OFF:
                track_id, pitch = args
                velocity = curr_velocity[track_id]

                # Close all notes
                if pitch == ALL_NOTES:
                    if active_notes[track_id]:
                        for pitch, notes in active_notes[track_id].items():
                            for note in notes:
                                note.duration = time - note.time
                            tracks[track_id].notes.extend(notes)
                        active_notes[track_id].clear()
                    continue

                # Skip it if there is no active notes
                if not active_notes[track_id][pitch]:
                    continue

                # NOTE: There is no way to disambiguate duplicate notes
                # of the same pitch. Thus, we need a policy for
                # handling duplicate notes.

                # 'FIFO': (first in first out) close the earliest note
                elif self.duplicate_note_mode.lower() == "fifo":
                    note = active_notes[track_id][pitch].popleft()
                    note.duration = time - note.time
                    tracks[track_id].notes.append(note)

                # 'LIFO': (last in first out) close the latest note on
                elif self.duplicate_note_mode.lower() == "lifo":
                    note = active_notes[track_id][pitch].pop()
                    note.duration = time - note.time
                    tracks[track_id].notes.append(note)

                # 'close_all' - close all note on events
                elif self.duplicate_note_mode.lower() == "close_all":
                    for note in active_notes[track_id][pitch]:
                        note.duration = time - note.time
                        tracks[track_id].notes.append(note)
                    active_notes[track_id][pitch].clear()

            elif event == TIME_SHIFT:
                shift, = args
                time += shift

            elif event == VELOCITY:
                track_id, velocity = args
                curr_velocity[track_id] = int(velocity * velocity_factor)

            elif event == PROGRAM:
                track_id, program = args
                if not program_is_set[track_id]:
                    tracks[track_id].program = program
                    program_is_set[track_id] = True

            elif event == DRUM:
                track_id, = args
                tracks[track_id].is_drum = True

        # Extend zero-duration notes to minimum length
        for track in tracks.values():
            for note in track.notes:
                if note.duration < 1:
                    note.duration = 1

        # Sort the tracks and the notes
        if self.ignore_empty_tracks:
            track_list = [tracks[key] for key in sorted(tracks.keys())
                          if tracks[key].notes]
        else:
            track_list = [tracks[key] for key in range(max(tracks.keys()) + 1)]
        for track in track_list:
            track.notes.sort(
                key=attrgetter("time", "pitch", "duration", "velocity"))

        return Music(resolution=self.resolution, tracks=track_list)
