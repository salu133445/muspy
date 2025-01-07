"""Music class.

This module defines the core class of MusPy---the Music class, a
universal container for symbolic music.

Classes
-------

- Music

Variables
---------

- DEFAULT_RESOLUTION

"""
from collections import OrderedDict
from math import ceil, floor
from pathlib import Path
from typing import Any, Callable, List, TypeVar, Union, Dict
from copy import deepcopy
from re import sub
from warnings import warn

import numpy as np
from mido import MidiFile
from music21.stream import Stream
from numpy import ndarray
from pretty_midi import PrettyMIDI
from pypianoroll import Multitrack

from .base import ComplexBase
from .classes import (
    Annotation,
    Barline,
    Beat,
    DEFAULT_VELOCITY,
    KeySignature,
    Lyric,
    Metadata,
    Tempo,
    TimeSignature,
    Track,
    get_end_time,
)
from .annotations import Dynamic
from .outputs import save, synthesize, to_object, to_representation, write
from .visualization import show

DEFAULT_RESOLUTION = 24
MusicT = TypeVar("MusicT", bound="Music")

__all__ = ["Music", "DEFAULT_RESOLUTION"]

# pylint: disable=super-init-not-called


class Music(ComplexBase):
    """A universal container for symbolic music.

    This is the core class of MusPy. A Music object can be constructed
    in the following ways.

    - :meth:`muspy.Music`: Construct by setting values for attributes
    - :meth:`muspy.Music.from_dict`: Construct from a dictionary that
      stores the attributes and their values as key-value pairs
    - :func:`muspy.read`: Read from a MIDI, a MusicXML or an ABC file
    - :func:`muspy.load`: Load from a JSON or a YAML file saved by
      :func:`muspy.save`
    - :func:`muspy.from_object`: Convert from a `music21.Stream`,
      :class:`mido.MidiFile`, :class:`pretty_midi.PrettyMIDI` or
      :class:`pypianoroll.Multitrack` object

    Attributes
    ----------
    metadata : :class:`muspy.Metadata`, default: `Metadata()`
        Metadata.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    tempos : list of :class:`muspy.Tempo`, default: []
        Tempo changes.
    key_signatures : list of :class:`muspy.KeySignature`, default: []
        Key signatures changes.
    time_signatures : list of :class:`muspy.TimeSignature`, default: []
        Time signature changes.
    barlines : list of :class:`muspy.Barline`, default: []
        Barlines.
    beats : list of :class:`muspy.Beat`, default: []
        Beats.
    lyrics : list of :class:`muspy.Lyric`, default: []
        Lyrics.
    annotations : list of :class:`muspy.Annotation`, default: []
        Annotations.
    tracks : list of :class:`muspy.Track`, default: []
        Music tracks.
    real_time : bool, default: False
        Are the times of different objects in real time (seconds)?

    Note
    ----
    Indexing a Music object returns the track of a certain index. That
    is, ``music[idx]`` returns ``music.tracks[idx]``. Length of a Music
    object is the number of tracks. That is, ``len(music)``  returns
    ``len(music.tracks)``.

    """

    _attributes = OrderedDict(
        [
            ("metadata", Metadata),
            ("resolution", int),
            ("tempos", Tempo),
            ("key_signatures", KeySignature),
            ("time_signatures", TimeSignature),
            ("barlines", Barline),
            ("beats", Beat),
            ("lyrics", Lyric),
            ("annotations", Annotation),
            ("tracks", Track),
            ("real_time", bool),
        ]
    )
    _optional_attributes = [
        "metadata",
        "resolution",
        "tempos",
        "key_signatures",
        "time_signatures",
        "barlines",
        "beats",
        "lyrics",
        "annotations",
        "tracks",
        "real_time",
    ]
    _list_attributes = [
        "tempos",
        "key_signatures",
        "time_signatures",
        "barlines",
        "beats",
        "lyrics",
        "annotations",
        "tracks",
    ]

    def __init__(
        self,
        metadata: Metadata = None,
        resolution: int = None,
        tempos: List[Tempo] = None,
        key_signatures: List[KeySignature] = None,
        time_signatures: List[TimeSignature] = None,
        barlines: List[Barline] = None,
        beats: List[Beat] = None,
        lyrics: List[Lyric] = None,
        annotations: List[Annotation] = None,
        tracks: List[Track] = None,
        real_time: bool = False,
    ):
        self.metadata = metadata if metadata is not None else Metadata()
        self.resolution = resolution if resolution is not None else DEFAULT_RESOLUTION
        self.tempos = tempos if tempos is not None else []
        self.key_signatures = key_signatures if key_signatures is not None else []
        self.time_signatures = time_signatures if time_signatures is not None else []
        self.beats = beats if beats is not None else []
        self.barlines = barlines if barlines is not None else []
        self.lyrics = lyrics if lyrics is not None else []
        self.annotations = annotations if annotations is not None else []
        self.tracks = tracks if tracks is not None else []
        self.real_time = real_time

    def __len__(self) -> int:
        return len(self.tracks)

    def __getitem__(self, key: int) -> Track:
        return self.tracks[key]

    def __setitem__(self, key: int, value: Track):
        self.tracks[key] = value

    def __delitem__(self, key: int):
        del self.tracks[key]

    def get_real_time(self, time: int) -> float:
        """Return the given time in real time (seconds).

        This includes tempos, key signatures, time signatures, note
        offsets, lyrics and annotations. Assume 120 qpm (quarter notes
        per minute) if no tempo information is available.

        Parameters
        ----------
        time : int
            The time (in metrical time steps) to be
            converted into real time (seconds).

        """
        # If no tempo information is available, assume 120 qpm
        if not self.tempos:
            return 0.5 * time / self.resolution

        # Compute the real end time
        position = 0.0
        qpm = 120.0
        factor = 60.0 / self.resolution
        real_time = 0.0
        for tempo in self.tempos:
            if tempo.time >= time: # stop when we've reached a tempo marking past the desired time
                break
            real_time += (tempo.time - position) * factor / qpm
            position = tempo.time
            qpm = tempo.qpm
        real_time += (time - position) * factor / qpm

        return real_time

    def get_end_time(self, is_sorted: bool = False) -> int:
        """Return the time of the last event across all the tracks.

        This includes tempos, key signatures, time signatures, barlines,
        beats, lyrics, annotations, note offsets and chord offsets.

        Parameters
        ----------
        is_sorted : bool, default: False
            Whether all the list attributes are sorted.

        """
        if self.tracks:
            track_end_time = max(
                track.get_end_time(is_sorted = is_sorted) for track in self.tracks
            )
        else:
            track_end_time = 0

        end_time = max(
            get_end_time(list_ = self.tempos, is_sorted = is_sorted),
            get_end_time(list_ = self.key_signatures, is_sorted = is_sorted),
            get_end_time(list_ = self.time_signatures, is_sorted = is_sorted),
            get_end_time(list_ = self.barlines, is_sorted = is_sorted),
            get_end_time(list_ = self.beats, is_sorted = is_sorted),
            get_end_time(list_ = self.lyrics, is_sorted = is_sorted),
            get_end_time(list_ = self.annotations, is_sorted = is_sorted),
            track_end_time,
        )

        return end_time

    def get_real_end_time(self, is_sorted: bool = False) -> float:
        """Return the end time in real time (seconds).

        This includes tempos, key signatures, time signatures, note
        offsets, lyrics and annotations. Assume 120 qpm (quarter notes
        per minute) if no tempo information is available.

        Parameters
        ----------
        is_sorted : bool, default: False
            Whether all the list attributes are sorted.

        """
        return self.get_real_time(time = self.get_end_time(is_sorted = is_sorted))

    def infer_barlines(self: MusicT, overwrite: bool = False) -> MusicT:
        """Infer barlines from the time signatures.

        This assumes that there is a barline at each time signature
        change.

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing barlines.

        Returns
        -------
        Object itself.

        Raises
        ------
        ValueError
            If no time signature is found.

        """
        if not overwrite and self.beats:
            return self
        if not self.time_signatures:
            raise ValueError(
                "Cannot infer barlines as no time signature is found."
            )
        self.barlines = []
        for i, time_sign in enumerate(self.time_signatures):
            if i == len(self.time_signatures) - 1:
                end = self.get_end_time()
            else:
                end = self.time_signatures[i + 1].time
            # NOTE: `resolution`` denotes the number of time steps per
            # quarter note
            bar_length = (4 * self.resolution) * (
                time_sign.numerator / time_sign.denominator
            )
            for time in np.arange(time_sign.time, end, bar_length):
                self.barlines.append(Barline(time=int(round(time))))
        return self

    def infer_barlines_and_beats(
        self: MusicT, overwrite: bool = False
    ) -> MusicT:
        """Infer barlines and beats from the time signature changes.

        This assumes that there is a downbeat at each time signature
        change (this is not always true, e.g., for a pickup measure).
        Return an empty list if no time signature is found.

        Parameters
        ----------
        overwrite : bool, default: False
            Whether to overwrite existing barlines or beats.

        Returns
        -------
        Object itself.

        Raises
        ------
        ValueError
            If no time signature is found.

        """
        if not overwrite and (self.barlines or self.beats):
            return self
        if not self.time_signatures:
            raise ValueError(
                "Cannot infer barlines and beats as no time signature is "
                "found."
            )
        self.barlines = []
        self.beats = []
        for i, time_sign in enumerate(self.time_signatures):
            if i == len(self.time_signatures) - 1:
                end = self.get_end_time()
            else:
                end = self.time_signatures[i + 1].time
            # NOTE: `resolution`` denotes the number of time steps per
            # quarter note
            bar_length = (4 * self.resolution) * (
                time_sign.numerator / time_sign.denominator
            )
            for time in np.arange(time_sign.time, end, bar_length):
                self.barlines.append(Barline(time=int(round(time))))
            beat_length = 4 * self.resolution / time_sign.denominator
            for j, time in enumerate(np.arange(time_sign.time, end, beat_length)):
                self.beats.append(Beat(time=int(round(time)), is_downbeat=(j % time_sign.numerator == 0)))
        return self

    def adjust_resolution(
        self: MusicT,
        target: int = None,
        factor: float = None,
        rounding: Union[str, Callable] = "round",
    ) -> MusicT:
        """Adjust resolution and timing of all time-stamped objects.

        Parameters
        ----------
        target : int, optional
            Target resolution.
        factor : int or float, optional
            Factor used to adjust the resolution based on the formula:
            `new_resolution = old_resolution * factor`. For example, a
            factor of 2 double the resolution, and a factor of 0.5 halve
            the resolution.
        rounding : {'round', 'ceil', 'floor'} or callable, default:
        'round'
            Rounding mode.

        Returns
        -------
        Object itself.

        """
        if self.resolution is None:
            raise TypeError("`resolution` must be given.")
        if self.resolution < 0:
            raise ValueError("`resolution` must be positive.")

        if target is None and factor is None:
            raise ValueError("One of `target` and `factor` must be given.")
        if target is not None and factor is not None:
            raise ValueError("Only one of `target` and `factor` can be given.")

        if target is None and self.resolution == target:
            return self

        if rounding is None or rounding == "round":
            rounding = round
        elif rounding == "ceil":
            rounding = ceil
        elif rounding == "floor":
            rounding = floor
        elif isinstance(rounding, str):
            raise ValueError(f"Unrecognized rounding mode : {rounding} .")

        if target is not None:
            if not isinstance(target, int):
                raise TypeError("`target` must be an integer.")
            target_ = int(target)
            factor_ = target / self.resolution

        if factor is not None:
            new_resolution = float(self.resolution * factor)
            if not new_resolution.is_integer():
                raise ValueError(
                    f"`factor` must be a factor of the original resolution "
                    f"{self.resolution}, but got : {factor}."
                )
            factor_ = float(factor)
            target_ = int(new_resolution)

        self.resolution = int(target_)
        self.adjust_time(lambda time: rounding(time * factor_))  # type: ignore
        return self

    def clip(self: MusicT, lower: int = 0, upper: int = 127) -> MusicT:
        """Clip the velocity of each note for each track.

        Parameters
        ----------
        lower : int, default: 0
            Lower bound.
        upper : int, default: 127
            Upper bound.

        Returns
        -------
        Object itself.

        """
        for track in self.tracks:
            track.clip(lower, upper)
        return self

    def convert_to_real_time(self) -> MusicT:
        """
        Convert all times and durations in this object into real time (seconds).
        Returns a new :class:`muspy.Music` object. However, note that many
        methods of the :class:`muspy.Music` object work improperly or contain
        unexpected behavior.

        Returns
        -------
        New :class:`muspy.Music` object with altered times and durations.
        """

        # do we even need to convert
        if self.real_time:
            warn("Time values are already in real time (`real_time` = True).", RuntimeWarning)
            return self

        # we don't want to alter the original object
        music = deepcopy(self)

        # convert
        for i in range(len(self.key_signatures)):
            music.key_signatures[i].time = self.get_real_time(time = self.key_signatures[i].time)
        for i in range(len(self.time_signatures)):
            music.time_signatures[i].time = self.get_real_time(time = self.time_signatures[i].time)
        for i in range(len(self.beats)):
            music.beats[i].time = self.get_real_time(time = self.beats[i].time)
        for i in range(len(self.barlines)):
            music.barlines[i].time = self.get_real_time(time = self.barlines[i].time)
        for i in range(len(self.lyrics)):
            music.lyrics[i].time = self.get_real_time(time = self.lyrics[i].time)
        for i in range(len(self.annotations)):
            time_time_steps = self.annotations[i].time
            music.annotations[i].time = self.get_real_time(time = time_time_steps)
            if hasattr(self.annotations[i].annotation, "duration"):
                music.annotations[i].annotation.duration = self.get_real_time(time = time_time_steps + self.annotations[i].annotation.duration) - music.annotations[i].time
        for i in range(len(self.tracks)):
            for j in range(len(self.tracks[i].notes)):
                time_time_steps = self.tracks[i].notes[j].time
                music.tracks[i].notes[j].time = self.get_real_time(time = time_time_steps)
                music.tracks[i].notes[j].duration = self.get_real_time(time = time_time_steps + self.tracks[i].notes[j].duration) - music.tracks[i].notes[j].time
            for j in range(len(self.tracks[i].chords)):
                time_time_steps = self.tracks[i].chords[j].time
                music.tracks[i].chords[j].time = self.get_real_time(time = time_time_steps)
                music.tracks[i].chords[j].duration = self.get_real_time(time = time_time_steps + self.tracks[i].chords[j].duration) - music.tracks[i].chords[j].time
            for j in range(len(self.tracks[i].annotations)):
                time_time_steps = self.tracks[i].annotations[j].time
                music.tracks[i].annotations[j].time = self.get_real_time(time = time_time_steps)
                if hasattr(self.tracks[i].annotations[j].annotation, "duration"):
                    music.tracks[i].annotations[j].annotation.duration = self.get_real_time(time = time_time_steps + self.tracks[i].annotations[j].annotation.duration) - music.tracks[i].annotations[j].time
            for j in range(len(self.tracks[i].lyrics)):
                music.tracks[i].lyrics[j].time = self.get_real_time(time = self.tracks[i].lyrics[j].time)
        for i in range(len(self.tempos)):
            music.tempos[i].time = self.get_real_time(time = self.tempos[i].time)

        # update
        music.real_time = True
        music.resolution = None # resolution is irrelevant when in real time

        # return the music object with real times
        return music

    def realize_annotations(
            self,
            velocity_increase_factor: float = 2.0,
            accent_velocity_increase_factor: float = 1.5,
            pedal_duration_change_factor: float = 3.0,
            staccato_duration_change_factor: float = 5.0,
            default_dynamic: str = "mf",
            ) -> MusicT:
        """
        Realize all annotations through note velocities and durations.
        Returns a new :class:`muspy.Music` object.

        Parameters
        ----------
        velocity_increase_factor : float, default: 2.0
            factor by which to increase velocity when an annotation 
            GRADUALLY increases velocity (e.g. crescendo)
        accent_velocity_increase_factor : float, default: 1.5
            factor by which to increase velocity when an articulation 
            INSTANTANEOUSLY increases velocity
        pedal_duration_change_factor : float, default: 3.0
            factor by which the sustain pedal increases the duration of 
            each note
        staccato_duration_change_factor : float, default: 5.0
            factor by which a staccato decreases the duration of a note
        default_dynamic : str, default: 'mf'
            default dynamic marking
        
        Returns
        -------
        New :class:`muspy.Music` object with altered notes and chords (via their velocities and durations).
        """
        # deal with different dynamic markings
        dynamic_velocity_map = {
            "pppppp": 4, "ppppp": 8, "pppp": 12, "ppp": 16, "pp": 33, "p": 49, "mp": 64,
            "mf": 80, "f": 96, "ff": 112, "fff": 126, "ffff": 127, "fffff": 127, "ffffff": 127,
            "sfpp": 96, "sfp": 112, "sf": 112, "sff": 126, "sfz": 112, "sffz": 126, "fz": 112, "rf": 112, "rfz": 112,
            "fp": 96, "pf": 49, "s": DEFAULT_VELOCITY, "r": DEFAULT_VELOCITY, "z": DEFAULT_VELOCITY, "n": DEFAULT_VELOCITY, "m": DEFAULT_VELOCITY,
        }
        dynamic_dynamics = set(tuple(dynamic_velocity_map.keys())[:tuple(dynamic_velocity_map.keys()).index("ffffff") + 1]) # dynamics that are actually dynamic markings and not sudden dynamic hikes
        annotation_priorities = ("Dynamic", "SlurSpanner", "HairPinSpanner", "TempoSpanner", "Articulation", "PedalSpanner")

        # we don't want to alter the original object
        music = deepcopy(self)

        # iterate through tracks
        for track in music.tracks:

            # get note times
            note_times = sorted(list({note.time for note in track.notes})) # times of notes, sorted ascending, removing duplicates
            note_time_indicies = {note_time: i for i, note_time in enumerate(note_times)}
            all_annotations = track.annotations + music.annotations

            # create annotations by time
            annotations_by_time: Dict[int, List[Annotation]] = dict(zip(note_times, ([] for _ in range(len(note_times))))) # dictionary where keys are time and values are expressive feature annotation objects
            for annotation in sorted(all_annotations, key = lambda annotation: annotation.time): # sort staff and system level annotations
                if hasattr(annotation.annotation, "subtype"):
                    if annotation.annotation.subtype is None:
                        continue
                    else:
                        annotation.annotation.subtype = sub(pattern = "[^\w0-9]", repl = "", string = annotation.annotation.subtype.lower()) # clean up the subtype
                annotation_falls_on_note = (annotation.time in annotations_by_time.keys())
                if annotation_falls_on_note: # if this annotation falls on a note, add that annotation to annotations by time (which we care about)
                    annotations_by_time[annotation.time].append(annotation) # add annotation
                if hasattr(annotation.annotation, "duration"): # deal with duration
                    if (annotation.annotation.__class__.__name__ == "Dynamic") and (annotation.annotation.subtype not in dynamic_dynamics): # for sudden dynamic hikes do not fill with duration
                        continue
                    if annotation_falls_on_note: # get index of the note after the current time when annotation falls on a note
                        current_note_time_index = note_time_indicies[annotation.time] + 1
                    else: # get index of the note after the current time when annotation does not fall on a note
                        current_note_time_index = len(note_times) # default value
                        for note_time in note_times:
                            if note_time >= annotation.time: # first note time after the annotation time
                                current_note_time_index = note_time_indicies[note_time]
                                break
                    while current_note_time_index < len(note_times):
                        if note_times[current_note_time_index] >= (annotation.time + annotation.annotation.duration): # when the annotation does not have any more effect on the notes being played
                            break # break out of while loop
                        annotations_by_time[note_times[current_note_time_index]].append(annotation)
                        current_note_time_index += 1 # increment
                    del current_note_time_index

            # make sure all note times in annotations by time have a dynamic at index 0
            for i, note_time in enumerate(note_times):
                if not any((annotation.annotation.__class__.__name__ == "Dynamic" for annotation in annotations_by_time[note_time])): # if there is no dynamic
                    j = i - 1 # start index finder at the index before current
                    while not any((annotation.annotation.subtype in dynamic_dynamics for annotation in annotations_by_time[note_times[j]] if annotation.annotation.__class__.__name__ == "Dynamic")) and (j > -1): # look for previous note times with a dynamic
                        j -= 1 # decrement j
                    if (j == -1): # no notes with dynamics before this one, result to default values
                        dynamic_annotation = Dynamic(subtype = default_dynamic, velocity = dynamic_velocity_map[default_dynamic])
                    else: # we found a dynamic before this note time
                        dynamic_annotation = annotations_by_time[note_times[j]][0].annotation # we can assume the dynamic marking is at index 0 because of our sorting
                    annotations_by_time[note_time].insert(0, Annotation(time = note_time, annotation = dynamic_annotation)) # insert dynamic at position 0
                annotations_by_time[note_time] = sorted(annotations_by_time[note_time], key = lambda annotation: annotation_priorities.index(annotation.annotation.__class__.__name__) if (annotation.annotation.__class__.__name__ in annotation_priorities) else len(annotation_priorities)) # sort annotations by time in desired order
                if annotations_by_time[note_time][0].annotation.velocity is None: # make sure dynamic velocity is not none
                    annotations_by_time[note_time][0].annotation.velocity = dynamic_velocity_map[default_dynamic] # set to default velocity

            # given an object, update its duration and velocity according to the annotations
            def update_obj_by_annotations(obj):
                """Given an object, update its duration and velocity according to the annotations in this track."""

                # get a base velocity from the dynamic
                obj.velocity = annotations_by_time[obj.time][0].annotation.velocity # the first index is always the dynamic

                # go through the rest of the annotations present at the object
                for annotation in annotations_by_time[obj.time][1:]: # skip the first index, since we just dealt with it

                    # ensure that values are valid
                    if hasattr(annotation.annotation, "subtype"): # make sure subtype field is not none
                        if annotation.annotation.subtype is None:
                            continue

                    # HairPinSpanner and TempoSpanner; changes in velocity
                    if (annotation.annotation.__class__.__name__ in ("HairPinSpanner", "TempoSpanner")): # some TempoSpanners involve a velocity change, so that is included here as well
                        if annotation.group is None: # since we aren't storing anything there anyways
                            end_velocity = obj.velocity # default is no change
                            if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("allarg", "cr"))): # increase-volume; allargando, crescendo
                                end_velocity *= velocity_increase_factor
                            elif any((annotation.annotation.subtype.startswith(prefix) for prefix in ("smorz", "dim", "decr"))): # decrease-volume; smorzando, diminuendo, decrescendo
                                end_velocity /= velocity_increase_factor
                            denominator = (annotation.time + annotation.annotation.duration) - obj.time
                            annotation.group = lambda time: (((end_velocity - obj.velocity) / denominator) * (time - obj.time)) + obj.velocity if (denominator != 0) else end_velocity # we will use group to store a lambda function to calculate velocity
                        obj.velocity += annotation.group(time = obj.time)

                    # SlurSpanner
                    elif annotation.annotation.__class__.__name__ == "SlurSpanner":
                        current_obj_time_index = note_time_indicies[obj.time]
                        if current_obj_time_index < len(note_times) - 1: # elsewise, there is no next note to slur to
                            obj.duration = note_times[current_obj_time_index + 1] - note_times[current_obj_time_index]
                        del current_obj_time_index

                    # PedalSpanner
                    elif annotation.annotation.__class__.__name__ == "PedalSpanner":
                        obj.duration *= pedal_duration_change_factor

                    # Articulation
                    elif annotation.annotation.__class__.__name__ == "Articulation":
                        if any((keyword in annotation.annotation.subtype for keyword in ("staccato", "staccatissimo", "spiccato", "pizzicato", "plucked", "marcato", "sforzato"))): # shortens note length
                            obj.duration /= staccato_duration_change_factor
                        if any((keyword in annotation.annotation.subtype for keyword in ("marcato", "sforzato", "accent"))): # increases velocity
                            obj.velocity += obj.velocity * (max((accent_velocity_increase_factor * (0.8 if "soft" in annotation.annotation.subtype else 1)), 1) - 1)
                        if "spiccato" in annotation.annotation.subtype: # decreases velocity
                            obj.velocity /= accent_velocity_increase_factor
                        if "tenuto" in annotation.annotation.subtype:
                            pass # the duration is full duration
                        # if "wiggle" in annotation.annotation.subtype: # vibrato and sawtooth
                        #     pass # currently no implementation
                        # if "portato" in annotation.annotation.subtype:
                        #     pass # currently no implementation
                        # if "trill" in annotation.annotation.subtype:
                        #     pass # currently no implementation
                        # if "mordent" in annotation.annotation.subtype:
                        #     pass # currently no implementation
                        # if "close" in annotation.annotation.subtype: # reference to a mute
                        #     pass # currently no implementation
                        # if any((keyword in annotation.annotation.subtype for keyword in ("open", "ouvert"))): # reference to a mute
                        #     pass # currently no implementation

                    # TechAnnotation
                    # elif annotation.annotation.__class__.__name__ == "TechAnnotation":
                    #     pass # currently no implementation since we so rarely encounter these

            # iterate through notes
            for note in track.notes:
                update_obj_by_annotations(obj = note)

            # iterate through chords
            for chord in track.chords:
                update_obj_by_annotations(obj = chord)

        # return the music object with realized annotations by time
        return music

    def transpose(self: MusicT, semitone: int) -> MusicT:
        """Transpose all the notes by a number of semitones.

        Parameters
        ----------
        semitone : int
            Number of semitones to transpose the notes. A positive value
            raises the pitches, while a negative value lowers the
            pitches.

        Returns
        -------
        Object itself.

        Notes
        -----
        Drum tracks are skipped.

        """
        for track in self.tracks:
            if not track.is_drum:
                track.transpose(semitone)
        return self

    def trim(self: MusicT, end: int) -> MusicT:
        """Trim the track.

        Parameters
        ----------
        end : int
            End time, excluding (i.e, the max time will be `end` - 1).

        Returns
        -------
        Object itself.

        """
        self.tempos = [x for x in self.tempos if x.time < end]
        self.key_signatures = [x for x in self.key_signatures if x.time < end]
        self.time_signatures = [
            x for x in self.time_signatures if x.time < end
        ]
        self.barlines = [x for x in self.barlines if x.time < end]
        self.beats = [x for x in self.beats if x.time < end]
        self.lyrics = [x for x in self.lyrics if x.time < end]
        self.annotations = [x for x in self.annotations if x.time < end]
        for track in self.tracks:
            track.trim(end)
        return self

    def save(self, path: Union[str, Path], kind: str = None, **kwargs: Any):
        """Save loselessly to a JSON or a YAML file.

        Refer to :func:`muspy.save` for full documentation.

        """
        return save(path, self, kind=kind, **kwargs)

    def save_json(self, path: Union[str, Path], **kwargs: Any):
        """Save loselessly to a JSON file.

        Refer to :func:`muspy.save_json` for full documentation.

        """
        return save(path, self, kind="json", **kwargs)

    def save_yaml(self, path: Union[str, Path]):
        """Save loselessly to a YAML file.

        Refer to :func:`muspy.save_yaml` for full documentation.

        """
        return save(path, self, kind="yaml")

    def write(self, path: Union[str, Path], kind: str = None, **kwargs: Any):
        """Write to a MIDI, a MusicXML, an ABC or an audio file.

        Refer to :func:`muspy.write` for full documentation.

        """
        return write(path, self, kind=kind, **kwargs)

    def write_midi(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MIDI file.

        Refer to :func:`muspy.write_midi` for full documentation.

        """
        return write(path, self, kind="midi", **kwargs)

    def write_musicxml(self, path: Union[str, Path], **kwargs: Any):
        """Write to a MusicXML file.

        Refer to :func:`muspy.write_musicxml` for full documentation.

        """
        return write(path, self, kind="musicxml", **kwargs)

    def write_abc(self, path: Union[str, Path], **kwargs: Any):
        """Write to an ABC file.

        Refer to :func:`muspy.write_abc` for full documentation.

        """
        return write(path, self, kind="abc", **kwargs)

    def write_audio(self, path: Union[str, Path], **kwargs: Any):
        """Write to an audio file.

        Refer to :func:`muspy.write_audio` for full documentation.

        """
        return write(path, self, kind="audio", **kwargs)

    def to_object(self, kind: str, **kwargs: Any):
        """Return as an object in other libraries.

        Refer to :func:`muspy.to_object` for full documentation.

        """
        return to_object(self, kind=kind, **kwargs)

    def to_music21(self, **kwargs: Any) -> Stream:
        """Return as a Stream object.

        Refer to :func:`muspy.to_music21` for full documentation.

        """
        return to_object(self, kind="music21", **kwargs)

    def to_mido(self, **kwargs: Any) -> MidiFile:
        """Return as a MidiFile object.

        Refer to :func:`muspy.to_mido` for full documentation.

        """
        return to_object(self, kind="mido", **kwargs)

    def to_pretty_midi(self, **kwargs: Any) -> PrettyMIDI:
        """Return as a PrettyMIDI object.

        Refer to :func:`muspy.to_pretty_midi` for full documentation.

        """
        return to_object(self, kind="pretty_midi", **kwargs)

    def to_pypianoroll(self, **kwargs: Any) -> Multitrack:
        """Return as a Multitrack object.

        Refer to :func:`muspy.to_pypianoroll` for full documentation.

        """
        return to_object(self, kind="pypianoroll", **kwargs)

    def to_representation(self, kind: str, **kwargs: Any) -> ndarray:
        """Return in a specific representation.

        Refer to :func:`muspy.to_representation` for full documentation.

        """
        return to_representation(self, kind=kind, **kwargs)

    def to_pitch_representation(self, **kwargs: Any) -> ndarray:
        """Return in pitch-based representation.

        Refer to :func:`muspy.to_pitch_representation` for full
        documentation.

        """
        return to_representation(self, kind="pitch", **kwargs)

    def to_pianoroll_representation(self, **kwargs: Any) -> ndarray:
        """Return in piano-roll representation.

        Refer to :func:`muspy.to_pianoroll_representation` for full
        documentation.

        """
        return to_representation(self, kind="piano-roll", **kwargs)

    def to_event_representation(self, **kwargs: Any) -> ndarray:
        """Return in event-based representation.

        Refer to :func:`muspy.to_event_representation` for full
        documentation.

        """
        return to_representation(self, kind="event", **kwargs)

    def to_note_representation(self, **kwargs: Any) -> ndarray:
        """Return in note-based representation.

        Refer to :func:`muspy.to_note_representation` for full
        documentation.

        """
        return to_representation(self, kind="note", **kwargs)

    def show(self, kind: str, **kwargs: Any):
        """Show visualization.

        Refer to :func:`muspy.show` for full documentation.

        """
        return show(self, kind, **kwargs)

    def show_score(self, **kwargs: Any):
        """Show score visualization.

        Refer to :func:`muspy.show_score` for full documentation.

        """
        return show(self, kind="score", **kwargs)

    def show_pianoroll(self, **kwargs: Any):
        """Show pianoroll visualization.

        Refer to :func:`muspy.show_pianoroll` for full documentation.

        """
        return show(self, kind="piano-roll", **kwargs)

    def synthesize(self, **kwargs) -> ndarray:
        """Synthesize a Music object to raw audio.

        Refer to :func:`muspy.synthesize` for full documentation.

        """
        return synthesize(self, **kwargs)
