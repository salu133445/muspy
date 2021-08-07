from collections import defaultdict, deque
from operator import attrgetter, itemgetter
from typing import DefaultDict, List, Optional, Sequence, Tuple, Union, cast
import warnings

from bidict import frozenbidict

from ..classes import Note, Track
from ..music import DEFAULT_RESOLUTION, Music


__all__ = [
    "AdvancedEventRepresentationProcessor",
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

Event = Tuple


def _event_to_str(event: Event) -> str:
    return ":".join(str(x) for x in event)


def _event_from_str(s: str) -> Event:
    event, *str_args = s.split(":")
    args = [int(x) for x in str_args]
    return (event, *args)


class AdvancedEventRepresentationProcessor:
    """Advanced event-based representation processor with multi-track
    support.

    The advanced event-based represetantion represents music as a
    sequence of events, including note-on, note-off, time-shift and
    velocity events. Compared to :class:`EventRepresentationProcessor`,
    it has support for multiple tracks and provides 3 different
    encoding formats: tuples, strings and integers.

    The following events are possible (written in the tuple format, as
    returned by :meth:`encode_as_tuples`):

    * `("note_on", track_id, pitch)` – note onset
    * `("note_off", track_id, pitch)` – note offset
    * `("velocity", track_id, velocity)` – set velocity for the
      following notes
    * `("program", track_id, program)` – set the :class:`Track`'s
      `program`
    * `("drum", track_id)` – set :class:`Track`'s `is_drum` to `True`
    * `("time_shift", ticks)` – move forward in time by the given
      number of ticks

    The :meth:`encode_as_strings` method equivalently formats these
    tuples as strings. The :meth:`encode` method returns a list of
    integer IDs, mapped according to the `vocab` dictionary.
    `vocab` is a bidirectional dictionary which allows accessing
    the inverse mapping as `vocab.inverse`.

    With `encode_velocity=True`, :class:`EventRepresentationProcessor`
    and :class:`AdvancedEventRepresentationProcessor` are equivalent.

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
    num_tracks: int or None
        The maximum number of tracks. Defaults to None, which means
        single-track mode (encode all events as if they were in one
        track).
    ignore_empty_tracks: bool
        Whether empty tracks should be ignored when encoding and deleted
        when decoding. Defaults to False.
    resolution: int
        Time steps per quarter note to use when decoding. Defaults to
        `muspy.DEFAULT_RESOLUTION`.
    check_resolution: bool
        Whether to check the resolution of the music when encoding.
        If True and if the resolution is not correct, an error will be
        raised. Defaults to True.
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
        check_resolution: bool = True,
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
        self.check_resolution = check_resolution
        self.duplicate_note_mode = duplicate_note_mode

        if encode_instrument and num_tracks is None:
            raise ValueError(
                'Cannot encode instruments when num_tracks is None')

        # Create vocabulary of events
        vocab_list: List[Event] = []
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
        if encode_velocity:
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
        self.vocab: frozenbidict[Event, int] = frozenbidict(
            enumerate(vocab_list)).inverse

    def encode_as_tuples(self, music: Music) -> List[Event]:
        """Encode a Music object into event-based representation
        encoded as a list of tuples.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        list of tuples
            List of event tuples.
        """
        if self.check_resolution and music.resolution != self.resolution:
            raise ValueError(
                "Expected a resolution of {} TPQN, got {}. ".format(
                    self.resolution, music.resolution)
                + "Set check_resolution=False to disable this check")

        # Create a list for all events
        events: List[Event] = []

        # Collect notes by track
        if self.num_tracks is None:
            # Put all notes in one track
            tracks = [[n for track in music.tracks for n in track.notes]]
        else:
            # Keep only num_tracks non-empty tracks
            track_objs = music.tracks
            if self.ignore_empty_tracks:
                track_objs = [track for track in track_objs if track.notes]
            if len(track_objs) > self.num_tracks:
                warnings.warn(
                    f"Number of tracks ({len(track_objs)}) exceeds num_tracks "
                    f"({self.num_tracks}). ", RuntimeWarning)
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

        # Sort the notes
        note_key_fn = attrgetter("time", "pitch", "duration", "velocity")
        notes.sort(key=lambda n_tr: (note_key_fn(n_tr[0]), n_tr[1]))

        # Collect note-related events
        note_events: List[Tuple[int, Event]] = []
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

        return events

    def encode(self, music: Music) -> List[int]:
        """Encode a Music object into event-based representation
        encoded as a list of integers.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        list of integers
            List of integer IDs.
        """
        return [self.vocab[e] for e in self.encode_as_tuples(music)]

    def encode_as_strings(self, music: Music) -> List[str]:
        """Encode a Music object into event-based representation
        encoded as a list of string tokens.

        Each token is formed from an event tuple by joining its items
        with a colon.

        Parameters
        ----------
        music : :class:`muspy.Music` object
            Music object to encode.

        Returns
        -------
        list of strings
            List of event tokens.
        """
        return [_event_to_str(e) for e in self.encode_as_tuples(music)]

    def decode(
        self, events: Sequence[Union[Event, str, int]]
    ) -> Music:
        """Decode event-based representation into a Music object.

        Parameters
        ----------
        list
            List of event tuples, strings or integers.

        Returns
        -------
        :class:`muspy.Music` object
            Decoded Music object.
        """
        if len(events) > 0:
            if isinstance(events[0], int):
                # Convert integers to events, skip unknown
                vocab_inv = self.vocab.inverse
                events = [vocab_inv[e] for e in cast(Sequence[int], events)
                          if e in vocab_inv]
            elif isinstance(events[0], str):
                events = [_event_from_str(s)
                          for s in cast(Sequence[str], events)]

        # Decode events, keeping track of information for each track
        time = 0  # Time is common for all tracks
        curr_velocity: DefaultDict[int, int] = defaultdict(
            lambda: self.default_velocity)
        velocity_factor = 128 / self.velocity_bins
        tracks: DefaultDict[int, Track] = defaultdict(lambda: Track(
            program=self.default_program,
            is_drum=self.default_is_drum))
        program_is_set: DefaultDict[int, bool] = defaultdict(bool)

        # Keep track of active note on messages for each track
        active_notes: DefaultDict[int, DefaultDict[int, deque]] = \
            defaultdict(lambda: defaultdict(deque))

        # Iterate over the events
        for (event, *args) in cast(Sequence[Event], events):
            if (event, *args) not in self.vocab:
                raise ValueError(f'Event {(event, *args):!r} not found in vocabulary')

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
