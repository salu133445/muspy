"""MIDI output interface."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union, Dict, List
from re import sub
from copy import deepcopy
from math import sin, pi

import numpy as np
from miditoolkit import Instrument as MtkInstrument
from miditoolkit import KeySignature as MtkKeySignature
from miditoolkit import Lyric as MtkLyric
from miditoolkit import Note as MtkNote
from miditoolkit import TempoChange as MtkTempo
from miditoolkit import TimeSignature as MtkTimeSignature
from miditoolkit.midi.parser import MidiFile as MtkMidiFile
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo, second2tick, MAX_PITCHWHEEL
from pretty_midi import Instrument as PmInstrument
from pretty_midi import KeySignature as PmKeySignature
from pretty_midi import Lyric as PmLyric
from pretty_midi import Note as PmNote
from pretty_midi import Text as PmText
from pretty_midi import PrettyMIDI
from pretty_midi import TimeSignature as PmTimeSignature
from pretty_midi import key_name_to_key_number

from ..classes import (
    Annotation,
    DEFAULT_VELOCITY,
    KeySignature,
    Lyric,
    Note,
    Tempo,
    TimeSignature,
    Track,
)
from ..annotations import Dynamic
from ..utils import CIRCLE_OF_FIFTHS

if TYPE_CHECKING:
    from ..music import Music

PITCH_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"] # names of notes
DRUM_CHANNEL = 9 # MIDI Drum Channel
FERMATA_TEMPO_SLOWDOWN = 3 # factor by which to slow down the tempo when there is a fermata
N_NOTES = 128 # number of notes for midi
RESOLUTION = 12 # resolution for MusicRender
PEDAL_DURATION_CHANGE_FACTOR = 3 # factor by which the sustain pedal increases the duration of each note
STACCATO_DURATION_CHANGE_FACTOR = 5 # factor by which a staccato decreases the duration of a note
VELOCITY_INCREASE_FACTOR = 2 # factor by which to increase velocity when an expressive feature GRADUALLY increases velocity
ACCENT_VELOCITY_INCREASE_FACTOR = 1.5 # factor by which to increase velocity when an accent INSTANTANEOUSLY increases velocity
FRACTION_TO_WIGGLE = 0.34 # fraction of MAX/MIN_PITCHWHEEL to bend notes for wiggle articulations (vibratos and sawtooths)
DEFAULT_QPM = 120 # default quarter notes per minute
DEFAULT_TEMPO = bpm2tempo(bpm = DEFAULT_QPM) # converted from qpm to tempo
N_TEMPO_SPANNER_SUBDIVISIONS = 5 # number of subdivisions for increasing/decreasing tempo with a tempo spanner
GRACE_NOTE_FORWARD_SHIFT_CONSTANT = 0.15 # fraction of a quarter note's duration to shift a note forward if it is a grace note
SWING_PROPORTION = 0.6666666667 # on what fraction of a beat does a swung eight note fall
OPTIMAL_RESOLUTION = 480 # we don't want too small of a resolution, or it's hard to apply expressive features
MAX_VELOCITY = 127 # maximum velocity for midi
DEFAULT_DYNAMIC = "mf" # not to be confused with representation.DEFAULT_DYNAMIC
DYNAMIC_VELOCITY_MAP = {
    "pppppp": 4, "ppppp": 8, "pppp": 12, "ppp": 16, "pp": 33, "p": 49, "mp": 64,
    "mf": 80, "f": 96, "ff": 112, "fff": 126, "ffff": 127, "fffff": 127, "ffffff": 127,
    "sfpp": 96, "sfp": 112, "sf": 112, "sff": 126, "sfz": 112, "sffz": 126, "fz": 112, "rf": 112, "rfz": 112,
    "fp": 96, "pf": 49, "s": DEFAULT_VELOCITY, "r": DEFAULT_VELOCITY, "z": DEFAULT_VELOCITY, "n": DEFAULT_VELOCITY, "m": DEFAULT_VELOCITY,
}
DYNAMIC_DYNAMICS = set(tuple(DYNAMIC_VELOCITY_MAP.keys())[:tuple(DYNAMIC_VELOCITY_MAP.keys()).index("ffffff") + 1]) # dynamics that are actually dynamic markings and not sudden dynamic hikes
ANNOTATION_PRIORITIES = ("Dynamic", "SlurSpanner", "HairPinSpanner", "TempoSpanner", "Articulation", "PedalSpanner")


def clean_up_subtype(subtype: str) -> str:
    """Clean up the subtype of an annotation so that I can better match for substrings."""
    return sub(pattern = "[^\w0-9]", repl = "", string = subtype.lower())


def sort_annotations_key(annotation: Annotation) -> int:
    """
    When given an annotation, associate the annotation with a certain number
    so that a list of annotations can be sorted in a desired order.
    """
    if annotation.annotation.__class__.__name__ in ANNOTATION_PRIORITIES:
        return ANNOTATION_PRIORITIES.index(annotation.annotation.__class__.__name__)
    else:
        return len(ANNOTATION_PRIORITIES)


def get_wiggle_func(articulation_subtype: str, amplitude: float = FRACTION_TO_WIGGLE * MAX_PITCHWHEEL, resolution: float = RESOLUTION) -> Callable:
    """
    Return the function that given a time, returns the amount of
    pitchbend for wiggle functions (vibrato or sawtooth).
    """
    period = resolution / 3
    if ("fast" in articulation_subtype) or ("wide" not in articulation_subtype):
        period /= 2
    if "sawtooth" in articulation_subtype: # sawtooth
        wiggle_func = lambda time: int(amplitude * ((time % period) / period))
    else: # vibrato is default
        wiggle_func = lambda time: int(amplitude * sin(time * (2 * pi / period)))
    return wiggle_func


def get_annotations_by_time(note_times: list, all_annotations: list) -> Dict[int, List[Annotation]]:
    """
    Return a dictionary where the keys are the set of note times,
    and the values are the expressive features present at that note time.
    """

    # create expressive features
    note_time_indicies = {note_time: i for i, note_time in enumerate(note_times)}
    annotations_by_time: Dict[int, List[Annotation]] = dict(zip(note_times, ([] for _ in range(len(note_times))))) # dictionary where keys are time and values are expressive feature annotation objects
    for annotation in sorted(all_annotations, key = lambda annotation: annotation.time): # sort staff and system level annotations
        if hasattr(annotation.annotation, "subtype"):
            if annotation.annotation.subtype is None:
                continue
            else:
                annotation.annotation.subtype = clean_up_subtype(subtype = annotation.annotation.subtype) # clean up the subtype
        annotation_falls_on_note = (annotation.time in annotations_by_time.keys())
        if annotation_falls_on_note and annotation.annotation.__class__.__name__ != "Articulation": # if this annotation falls on a note, add that annotation to expressive features (which we care about)
            annotations_by_time[annotation.time].append(annotation) # add annotation
        if hasattr(annotation.annotation, "duration"): # deal with duration
            if (annotation.annotation.__class__.__name__ == "Dynamic") and (annotation.annotation.subtype not in DYNAMIC_DYNAMICS): # for sudden dynamic hikes do not fill with duration
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

    # make sure all note times in expressive features have a dynamic at index 0
    for i, note_time in enumerate(note_times):
        if not any((annotation.annotation.__class__.__name__ == "Dynamic" for annotation in annotations_by_time[note_time])): # if there is no dynamic
            j = i - 1 # start index finder at the index before current
            while not any((annotation.annotation.subtype in DYNAMIC_DYNAMICS for annotation in annotations_by_time[note_times[j]] if annotation.annotation.__class__.__name__ == "Dynamic")) and (j > -1): # look for previous note times with a dynamic
                j -= 1 # decrement j
            if (j == -1): # no notes with dynamics before this one, result to default values
                dynamic_annotation = Dynamic(subtype = DEFAULT_DYNAMIC, velocity = DYNAMIC_VELOCITY_MAP[DEFAULT_DYNAMIC])
            else: # we found a dynamic before this note time
                dynamic_annotation = annotations_by_time[note_times[j]][0].annotation # we can assume the dynamic marking is at index 0 because of our sorting
            annotations_by_time[note_time].insert(0, Annotation(time = note_time, annotation = dynamic_annotation)) # insert dynamic at position 0
        annotations_by_time[note_time] = sorted(annotations_by_time[note_time], key = sort_annotations_key) # sort expressive features in desired order
        if annotations_by_time[note_time][0].annotation.velocity is None: # make sure dynamic velocity is not none
            annotations_by_time[note_time][0].annotation.velocity = DYNAMIC_VELOCITY_MAP[DEFAULT_DYNAMIC] # set to default velocity

    return annotations_by_time


def to_delta_time(midi_track: MidiTrack, ticks_per_beat: int, real_time: bool = False):
    """Convert a mido MidiTrack object from absolute time to delta time.

    Parameters
    ----------
    midi_track : :class:`mido.MidiTrack` object
        mido MidiTrack object to convert.
    ticks_per_beat : int
        Number of MIDI ticks per beat.
    real_time : bool, default: False
        Is the provided .mid file in real time (seconds) or metrical time (time_steps)?

    """

    # sort messages by time
    midi_track.sort(key = lambda message: message.time)

    # convert seconds to ticks if necessary
    if real_time:
        for message in midi_track:
            message.time = second2tick(second = message.time, ticks_per_beat = ticks_per_beat, tempo = DEFAULT_TEMPO)

    # convert to delta time
    time = 0
    for message in midi_track:
        time_ = message.time
        message.time = int(message.time - time) # ensure message time is int
        time = time_


def to_mido_note_on_note_off(note: Note, channel: int, use_note_off_message: bool = False) -> Tuple[Message, Message]:
    """Return a Note object as mido Message objects.

    Timing is NOT in delta time.

    Parameters
    ----------
    note : :class:`Note` object
        Note object to convert.
    channel : int
        Channel of the .mid message.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages with zero velocity are used instead. The advantage to using note-on messages at zero velocity is that it can avoid sending additional status bytes when Running Status is employed.

    Returns
    -------
    :class:`mido.Message` object
        Converted mido Message object for note on.
    :class:`mido.Message` object
        Converted mido Message object for note off.

    """

    # deal with velocity
    velocity = note.velocity # copy of velocity as to not alter the music object
    if velocity is None:
        velocity = DEFAULT_VELOCITY
    velocity = int(max(min(velocity, MAX_VELOCITY), 0)) # make sure velocity is within valid range and an integer

    # deal with note
    pitch = note.pitch
    pitch = int(max(min(pitch, N_NOTES - 1), 0)) # make sure the note is within valid range and an integer

    # note on message
    note_on_msg = Message(type = "note_on", time = note.time, note = pitch, velocity = velocity, channel = channel) # create note on message

    # note off message
    if use_note_off_message: # create note off message
        note_off_msg = Message(type = "note_off", time = note.time + note.duration, note = pitch, velocity = velocity, channel = channel)
    else:
        note_off_msg = Message(type = "note_on", time = note.time + note.duration, note = pitch, velocity = 0, channel = channel)

    # return messages
    return note_on_msg, note_off_msg


def to_mido_meta_track(music: "Music", realize_annotations: bool = False) -> MidiTrack:
    """Return a mido MidiTrack containing metadata of a Music object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?

    Returns
    -------
    :class:`mido.MidiTrack` object
        Converted mido MidiTrack object.

    """

    # create a track to store the metadata
    meta_track = MidiTrack()
    all_notes = sum((track.notes for track in music.tracks), []) # all notes
    if len(all_notes) == 0:
        return meta_track
    else:
        max_note_time = max((note.time for note in all_notes))

    # song title
    if music.metadata.title is not None:
        meta_track.append(MetaMessage(type = "track_name", name = music.metadata.title))

    # tempos and time signatures
    metrical_time = (not music.real_time)
    if metrical_time:
        combined_temporal_features = list(filter(lambda temporal_feature: temporal_feature.time <= max_note_time, music.tempos + music.time_signatures))
        combined_temporal_features = sorted(combined_temporal_features, key = lambda temporal_feature: temporal_feature.time) # get sorted list of tempos and time signatures
        # current_time_signature = music.time_signatures[0] if len(music.time_signatures) > 0 else TimeSignature(time = 0) # instantiate current_time_signature
        tempo_times = [] # keep track of tempo event times for tempo spanners later
        tempo_changes = [] # keep track of tempo changes to deal with tempo spanners later
        for temporal_feature in combined_temporal_features:
            if isinstance(temporal_feature, Tempo) and temporal_feature.qpm > 0: # if tempo feature
                current_tempo = bpm2tempo(bpm = temporal_feature.qpm)
                meta_track.append(MetaMessage(type = "set_tempo", time = temporal_feature.time, tempo = current_tempo))
                tempo_times.append(temporal_feature.time)
                tempo_changes.append(current_tempo)
            elif isinstance(temporal_feature, TimeSignature): # if time signature
                meta_track.append(MetaMessage(type = "time_signature", time = temporal_feature.time, numerator = temporal_feature.numerator, denominator = temporal_feature.denominator))
                # current_time_signature = temporal_feature # update current_time_signature
    else:
        meta_track.append(MetaMessage(type = "set_tempo", time = 0, tempo = DEFAULT_TEMPO))

    # key signatures
    for key_signature in filter(lambda key_signature: key_signature.time <= max_note_time, music.key_signatures):
        if (key_signature.root is not None) and (key_signature.mode in ("major", "minor")):
            meta_track.append(MetaMessage(type = "key_signature", time = key_signature.time, key = PITCH_NAMES[key_signature.root] + ("m" if key_signature.mode == "minor" else "")))
        elif key_signature.fifths is not None:
            meta_track.append(MetaMessage(type = "key_signature", time = key_signature.time, key = PITCH_NAMES[CIRCLE_OF_FIFTHS[8 + key_signature.fifths][0]]))

    # lyrics
    for lyric in filter(lambda lyric: lyric.time <= max_note_time, music.lyrics):
        meta_track.append(MetaMessage(type = "lyrics", time = lyric.time, text = lyric.lyric))

    # system and staff level annotations
    if realize_annotations:
        current_tempo_index = 0
        for annotation in (music.annotations + sum((track.annotations for track in music.tracks), [])):

            # skip annotations out of the relevant time scope
            if annotation.time <= max_note_time:
                continue

            # ensure that values are valid
            annotation_type = annotation.annotation.__class__.__name__
            if hasattr(annotation.annotation, "subtype"): # make sure subtype field is not none
                if annotation.annotation.subtype is None:
                    continue
                else:
                    annotation.annotation.subtype = clean_up_subtype(subtype = annotation.annotation.subtype) # clean up the subtype

            # update current_tempo_index if necessary
            if metrical_time:
                if current_tempo_index < (len(tempo_times) - 1): # avoid index error later on at last element in tempo_times
                    if tempo_times[current_tempo_index + 1] <= annotation.time: # update current_tempo_index if necessary
                        current_tempo_index += 1 # increment

            # Text and TextSpanner
            if annotation_type in ("Text", "TextSpanner"):
                meta_track.append(MetaMessage(type = "text", time = annotation.time, text = annotation.annotation.text))

            # RehearsalMark
            elif annotation_type == "RehearsalMark":
                meta_track.append(MetaMessage(type = "marker", time = annotation.time, text = annotation.annotation.text))

            # if real time, temporal features have already been accounted for
            elif metrical_time:

                # Fermata and fermatas stored inside of Articulation
                if (annotation_type == "Fermata") or (annotation_type == "Articulation"): # only apply when metrical time in use
                    if (annotation_type == "Articulation") and ("fermata" not in annotation.annotation.subtype): # looking for fermatas hidden as articulations
                        continue # if not a fermata-articulation, skip
                    longest_note_duration_at_current_time = max([note.duration for note in all_notes if note.time == annotation.time] + [0]) # go through notes and find longest duration note at the time of the fermata
                    if longest_note_duration_at_current_time > 0:
                        meta_track.append(MetaMessage(type = "set_tempo", time = annotation.time, tempo = tempo_changes[current_tempo_index] * FERMATA_TEMPO_SLOWDOWN)) # start of fermata
                        meta_track.append(MetaMessage(type = "set_tempo", time = annotation.time + longest_note_duration_at_current_time, tempo = tempo_changes[current_tempo_index])) # end of fermata
                    del longest_note_duration_at_current_time

                # TempoSpanner
                elif annotation_type == "TempoSpanner": # only apply when metrical time in use
                    if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("lent", "rall", "rit", "smorz", "sost", "allarg"))): # slow-downs; lentando, rallentando, ritardando, smorzando, sostenuto, allargando
                        tempo_change_factor_fn = lambda t: t
                    elif any((annotation.annotation.subtype.startswith(prefix) for prefix in ("accel", "leg"))): # speed-ups; accelerando, leggiero
                        tempo_change_factor_fn = lambda t: 1 / t
                    else: # unknown TempoSpanner subtype
                        tempo_change_factor_fn = lambda t: 1
                    for time, tempo_change_factor_magnitude in zip(range(annotation.time, annotation.time + annotation.annotation.duration, int(annotation.annotation.duration / N_TEMPO_SPANNER_SUBDIVISIONS)), range(1, 1 + N_TEMPO_SPANNER_SUBDIVISIONS)):
                        meta_track.append(MetaMessage(type = "set_tempo", time = time, tempo = int(tempo_changes[current_tempo_index] * tempo_change_factor_fn(t = tempo_change_factor_magnitude)))) # add tempo change
                    end_tempo_spanner_tempo_index = current_tempo_index
                    if (current_tempo_index < (len(tempo_changes) - 1)) and ((annotation.time + annotation.annotation.duration) > tempo_times[current_tempo_index + 1]): # check if the tempo changed during the tempo spanner
                        end_tempo_spanner_tempo_index += 1 # if the tempo changed during the tempo spanner
                    meta_track.append(MetaMessage(type = "set_tempo", time = annotation.time + annotation.annotation.duration, tempo = tempo_changes[end_tempo_spanner_tempo_index])) # reset tempo
                    del time, tempo_change_factor_magnitude, tempo_change_factor_fn, end_tempo_spanner_tempo_index

        # clear up memory
        del current_tempo_index

    # clear up memory
    del all_notes

    # end of track message
    meta_track.append(MetaMessage(type = "end_of_track"))

    # convert to delta time
    to_delta_time(midi_track = meta_track, ticks_per_beat = music.resolution, real_time = music.real_time)

    return meta_track


def to_mido_track(
        track: Track,
        music: "Music",
        realize_annotations: bool = False,
        channel: int = None,
        use_note_off_message: bool = False
    ) -> MidiTrack:
    """Return a Track object as a mido MidiTrack object.

    Parameters
    ----------
    track : :class:`Track` object
        Track object to convert.
    music : :class:`muspy.Music` object
        Music object that `track` belongs to.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?
    channel : int, optional
        Channel number. Defaults to 10 for drums and 0 for other instruments.
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages with zero velocity are used instead. The advantage to using note-on messages at zero velocity is that it can avoid sending additional status bytes when Running Status is employed.

    Returns
    -------
    :class:`mido.MidiTrack` object
        Converted mido MidiTrack object.

    """

    # determine channel
    if channel is None:
        channel = DRUM_CHANNEL if track.is_drum else 0

    # create a new .mid track
    midi_track = MidiTrack()

    # track name messages
    if track.name is not None:
        midi_track.append(MetaMessage(type = "track_name", name = track.name))

    # program change messages
    midi_track.append(Message(type = "program_change", program = track.program, channel = channel))

    # deal with swing, but only if we are realizing annotations
    if realize_annotations:
        is_swung = False
        swing_features = list(filter(lambda annotation: (annotation.annotation.__class__.__name__ == "Text") and (annotation.annotation.is_system) and (annotation.annotation.style == "tempo"), music.annotations))
        swing_feature_index = -1
        for note in track.notes:
            if (swing_feature_index < (len(swing_features) - 1)) and (note.time >= swing_features[swing_feature_index + 1].time): # determine if we must update is_swung
                swing_feature_index += 1
                is_swung = (swing_features[swing_feature_index].annotation.text == "Swing") # update is_swung
            if is_swung and (((note.time / music.resolution) % 1) == 0.5): # add swing if we are swinging and the note falls on an off-beat eighth note
                note.time = int(max(0, note.time + (music.resolution * (SWING_PROPORTION - 0.5))))
        del is_swung, swing_features, swing_feature_index

    # deal with expressive features
    note_times = sorted(list({note.time for note in track.notes})) # times of notes, sorted ascending, removing duplicates
    note_time_indicies = {note_time: i for i, note_time in enumerate(note_times)}
    annotations_by_time = get_annotations_by_time(note_times = note_times, all_annotations = track.annotations + music.annotations) # dictionary where keys are time and values are expressive feature annotation objects

    # note on and note off messages
    for note in track.notes:

        # apply expressive features if desired
        if realize_annotations:

            # determine velocity from dynamic marking
            note.velocity = annotations_by_time[note.time][0].annotation.velocity # the first index is always the dynamic

            # get note notations as annotations
            note_notations_as_annotations = [Annotation(time = note.time, annotation = notation) for notation in note.notations] if note.notations is not None else []

            # iterate through note notations
            for annotation in annotations_by_time[note.time][1:] + note_notations_as_annotations: # skip the first index, since we just dealt with it

                # ensure that values are valid
                annotation_type = annotation.annotation.__class__.__name__
                if hasattr(annotation.annotation, "subtype"): # make sure subtype field is not none
                    if annotation.annotation.subtype is None:
                        continue

                # HairPinSpanner and TempoSpanner; changes in velocity
                if (annotation_type in ("HairPinSpanner", "TempoSpanner")) and music.infer_velocity: # some TempoSpanners involve a velocity change, so that is included here as well
                    if annotation.group is None: # since we aren't storing anything there anyways
                        end_velocity = note.velocity # default is no change
                        if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("allarg", "cr"))): # increase-volume; allargando, crescendo
                            end_velocity *= VELOCITY_INCREASE_FACTOR
                        elif any((annotation.annotation.subtype.startswith(prefix) for prefix in ("smorz", "dim", "decr"))): # decrease-volume; smorzando, diminuendo, decrescendo
                            end_velocity /= VELOCITY_INCREASE_FACTOR
                        denominator = (annotation.time + annotation.annotation.duration) - note.time
                        annotation.group = lambda time: (((((end_velocity - note.velocity) / denominator) * (time - note.time)) + note.velocity) if (denominator != 0) else end_velocity) # we will use group to store a lambda function to calculate velocity
                    note.velocity = annotation.group(time = note.time) # previously used +=

                # SlurSpanner
                elif annotation_type == "SlurSpanner":
                    if (note_time_indicies[note.time] == (len(note_times) - 1)) or not any(slur_spanner is annotation for slur_spanner in filter(lambda annotation_: annotation_.annotation.__class__.__name__ == "SlurSpanner", annotations_by_time[note_times[note_time_indicies[note.time] + 1]])):
                        continue # if the note is the last note in the slur, we don't want to slur it
                    current_note_time_index = note_time_indicies[note.time]
                    if current_note_time_index < len(note_times) - 1: # elsewise, there is no next note to slur to
                        note.duration = max(note_times[current_note_time_index + 1] - note_times[current_note_time_index], note.duration) # we don't want to make the note shorter
                    del current_note_time_index

                # PedalSpanner
                elif annotation_type == "PedalSpanner":
                    note.duration *= PEDAL_DURATION_CHANGE_FACTOR

                # Articulation
                elif annotation_type == "Articulation":
                    if any((keyword in annotation.annotation.subtype for keyword in ("staccato", "staccatissimo", "spiccato", "pizzicato", "plucked", "marcato", "sforzato"))): # shortens note length
                        note.duration /= STACCATO_DURATION_CHANGE_FACTOR
                    if any((keyword in annotation.annotation.subtype for keyword in ("marcato", "sforzato", "accent"))): # increases velocity
                        note.velocity *= max((ACCENT_VELOCITY_INCREASE_FACTOR * (0.8 if "soft" in annotation.annotation.subtype else 1)), 1)
                    if ("spiccato" in annotation.annotation.subtype): # decreases velocity
                        note.velocity /= ACCENT_VELOCITY_INCREASE_FACTOR
                    if "wiggle" in annotation.annotation.subtype: # vibrato and sawtooth
                        times = np.linspace(start = note.time, stop = note.time + note.duration, num = 8, endpoint = False)
                        pitch_func = get_wiggle_func(articulation_subtype = annotation.annotation.subtype, resolution = music.resolution)
                        for time in times:
                            midi_track.append(Message(type = "pitchwheel", time = time, pitch = pitch_func(time = time - times[0]), channel = channel))
                        midi_track.append(Message(type = "pitchwheel", time = note.time + note.duration, pitch = 0, channel = channel)) # reset pitch
                    if "tenuto" in annotation.annotation.subtype:
                        pass # the duration is full duration
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
                # elif annotation_type == "TechAnnotation":
                #     pass # currently no implementation since we so rarely encounter these

        # adjust note slightly if grace note
        if note.is_grace: # move the note slightly ahead if it is a grace note
            note.time = max(0, note.time - (music.resolution * GRACE_NOTE_FORWARD_SHIFT_CONSTANT)) # no grace notes on the first note, to avoid negative times

        # ensure note time is an integer
        note.time = int(note.time) # ensure note time is an integer

        # add note to track
        midi_track.extend(to_mido_note_on_note_off(note = note, channel = channel, use_note_off_message = use_note_off_message))

    # end of track message
    midi_track.append(MetaMessage(type = "end_of_track"))

    # convert to delta time
    to_delta_time(midi_track = midi_track, ticks_per_beat = music.resolution, real_time = music.real_time)

    return midi_track


def to_mido(music: "Music", realize_annotations: bool = False, use_note_off_message: bool = False):
    """Return a Music object as a MidiFile object.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

    Returns
    -------
    :class:`mido.MidiFile`
        Converted MidiFile object.

    """

    # ensure we are operating on a copy of the original musico object
    music = deepcopy(music)

    # redo resolution if it's too low
    if music.resolution < OPTIMAL_RESOLUTION and realize_annotations: # resolution is adjusted if annotations are being realized
        music.adjust_resolution(target = OPTIMAL_RESOLUTION)

    # create a .mid file object
    midi = MidiFile(type = 1, ticks_per_beat = music.resolution, charset = "utf8")

    # append meta track
    midi.tracks.append(to_mido_meta_track(music = music, realize_annotations = realize_annotations))

    # iterate over music tracks
    for i, track in enumerate(music.tracks):
        # NOTE: Many softwares use the same instrument for messages of the same channel in different tracks. Thus, we want to assign a unique channel number for each track. .mid has 15 channels for instruments other than drums, so we increment the channel number for each track (skipping the drum channel) and go back to 0 once we run out of channels.

        # assign channel number
        if track.is_drum:
            channel = DRUM_CHANNEL # mido numbers channels 0 to 15 instead of 1 to 16
        else:
            channel = i % 15 # .mid has 15 channels for instruments other than drums
            channel += int(channel >= DRUM_CHANNEL) # avoid drum channel by adding one if the channel is greater than 8

        # add track
        midi.tracks.append(to_mido_track(track = track, music = music, realize_annotations = realize_annotations, channel = channel, use_note_off_message = use_note_off_message))

    # return the midi object
    return midi


def write_midi_mido(
    path: Union[str, Path], music: "Music", realize_annotations: bool = False, use_note_off_message: bool = False
):
    """Write a Music object to a MIDI file using mido as backend.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to write.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?
    use_note_off_message : bool, default: False
        Whether to use note-off messages. If False, note-on messages
        with zero velocity are used instead. The advantage to using
        note-on messages at zero velocity is that it can avoid sending
        additional status bytes when Running Status is employed.

    """
    midi = to_mido(music = music, realize_annotations = realize_annotations, use_note_off_message = use_note_off_message)
    midi.save(str(path))


def to_pretty_midi_key_signature(
    key_signature: KeySignature, map_time: Callable = None
) -> Optional[PmKeySignature]:
    """Return a KeySignature object as a pretty_midi KeySignature."""
    # TODO: `key_signature.root_str` might be given
    if key_signature.root is None:
        return None
    if key_signature.mode not in ("major", "minor"):
        return None
    key_name = f"{PITCH_NAMES[key_signature.root]} {key_signature.mode}"
    if map_time is not None:
        time = map_time(key_signature.time)
    else:
        time = key_signature.time
    return PmKeySignature(
        key_number=key_name_to_key_number(key_name), time=time
    )


def to_pretty_midi_time_signature(
    time_signature: TimeSignature, map_time: Callable = None
) -> PmTimeSignature:
    """Return a TimeSignature object as a pretty_midi TimeSignature."""
    if map_time is not None:
        time = map_time(time_signature.time)
    else:
        time = time_signature.time
    return PmTimeSignature(
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
        time=time,
    )


def to_pretty_midi_lyric(lyric: Lyric, map_time: Callable = None) -> PmLyric:
    """Return a Lyric object as a pretty_midi Lyric object."""
    if map_time is not None:
        time = map_time(lyric.time)
    else:
        time = lyric.time
    return PmLyric(text=lyric.lyric, time=time)


def to_pretty_midi_note(note: Note, map_time: Callable = None) -> PmNote:
    """Return a Note object as a pretty_midi Note object."""
    if map_time is not None:
        start = map_time(note.start)
        end = map_time(note.end)
    else:
        start = note.start
        end = note.end
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    return PmNote(velocity=velocity, pitch=note.pitch, start=start, end=end,)


def to_pretty_midi_text(annotation: Annotation, map_time: Callable = None) -> PmText:
    """Return an Annotation object as a pretty_midi Text object."""
    time = map_time(annotation.time) if map_time is not None else annotation.time
    return PmText(text=annotation.annotation.text, time=time)


def to_pretty_midi_instrument(
    track: Track, music: "Music", map_time: Callable = None, realize_annotations: bool = False,
) -> PmInstrument:
    """Return a Track object as a pretty_midi Instrument object."""

    # create instrument
    instrument = PmInstrument(
        program=track.program, is_drum=track.is_drum, name=track.name
    )

    # deal with swing, but only if we are realizing annotations
    if realize_annotations:
        is_swung = False
        swing_features = list(filter(lambda annotation: (annotation.annotation.__class__.__name__ == "Text") and (annotation.annotation.is_system) and (annotation.annotation.style == "tempo"), music.annotations))
        swing_feature_index = -1
        for note in track.notes:
            if (swing_feature_index < (len(swing_features) - 1)) and (note.time >= swing_features[swing_feature_index + 1].time): # determine if we must update is_swung
                swing_feature_index += 1
                is_swung = (swing_features[swing_feature_index].annotation.text == "Swing") # update is_swung
            if is_swung and (((note.time / music.resolution) % 1) == 0.5): # add swing if we are swinging and the note falls on an off-beat eighth note
                note.time = int(max(0, note.time + (music.resolution * (SWING_PROPORTION - 0.5))))
        del is_swung, swing_features, swing_feature_index

    # deal with expressive features
    note_times = sorted(list({note.time for note in track.notes})) # times of notes, sorted ascending, removing duplicates
    note_time_indicies = {note_time: i for i, note_time in enumerate(note_times)}
    annotations_by_time = get_annotations_by_time(note_times = note_times, all_annotations = track.annotations + music.annotations) # dictionary where keys are time and values are expressive feature annotation objects

    # iterate through notes
    for note in track.notes:

        # determine velocity from dynamic marking
        note.velocity = annotations_by_time[note.time][0].annotation.velocity # the first index is always the dynamic

        # apply expressive features if desired
        if realize_annotations:
            for annotation in annotations_by_time[note.time][1:]: # skip the first index, since we just dealt with it

                # ensure that values are valid
                annotation_type = annotation.annotation.__class__.__name__
                if hasattr(annotation.annotation, "subtype"): # make sure subtype field is not none
                    if annotation.annotation.subtype is None:
                        continue

                # HairPinSpanner and TempoSpanner; changes in velocity
                if (annotation_type in ("HairPinSpanner", "TempoSpanner")) and music.infer_velocity: # some TempoSpanners involve a velocity change, so that is included here as well
                    if annotation.group is None: # since we aren't storing anything there anyways
                        end_velocity = note.velocity # default is no change
                        if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("allarg", "cr"))): # increase-volume; allargando, crescendo
                            end_velocity *= VELOCITY_INCREASE_FACTOR
                        elif any((annotation.annotation.subtype.startswith(prefix) for prefix in ("smorz", "dim", "decr"))): # decrease-volume; smorzando, diminuendo, decrescendo
                            end_velocity /= VELOCITY_INCREASE_FACTOR
                        denominator = (annotation.time + annotation.annotation.duration) - note.time
                        annotation.group = lambda time: (((((end_velocity - note.velocity) / denominator) * (time - note.time)) + note.velocity) if (denominator != 0) else end_velocity) # we will use group to store a lambda function to calculate velocity
                    note.velocity = annotation.group(time = note.time) # previously used +=

                # SlurSpanner
                elif annotation_type == "SlurSpanner":
                    if (note_time_indicies[note.time] == (len(note_times) - 1)) or not any(slur_spanner is annotation for slur_spanner in filter(lambda annotation_: annotation_.annotation.__class__.__name__ == "SlurSpanner", annotations_by_time[note_times[note_time_indicies[note.time] + 1]])):
                        continue # if the note is the last note in the slur, we don't want to slur it
                    current_note_time_index = note_time_indicies[note.time]
                    if current_note_time_index < len(note_times) - 1: # elsewise, there is no next note to slur to
                        note.duration = max(note_times[current_note_time_index + 1] - note_times[current_note_time_index], note.duration) # we don't want to make the note shorter
                    del current_note_time_index

                # PedalSpanner
                elif annotation_type == "PedalSpanner":
                    note.duration *= PEDAL_DURATION_CHANGE_FACTOR

                # Articulation
                elif annotation_type == "Articulation":
                    if any((keyword in annotation.annotation.subtype for keyword in ("staccato", "staccatissimo", "spiccato", "pizzicato", "plucked", "marcato", "sforzato"))): # shortens note length
                        note.duration /= STACCATO_DURATION_CHANGE_FACTOR
                    if any((keyword in annotation.annotation.subtype for keyword in ("marcato", "sforzato", "accent"))): # increases velocity
                        note.velocity *= max((ACCENT_VELOCITY_INCREASE_FACTOR * (0.8 if "soft" in annotation.annotation.subtype else 1)), 1)
                    if ("spiccato" in annotation.annotation.subtype): # decreases velocity
                        note.velocity /= ACCENT_VELOCITY_INCREASE_FACTOR
                    if "tenuto" in annotation.annotation.subtype:
                        pass # the duration is full duration
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
                # elif annotation_type == "TechAnnotation":
                #     pass # currently no implementation since we so rarely encounter these

        # adjust note slightly if grace note
        if note.is_grace: # move the note slightly ahead if it is a grace note
            note.time = max(0, note.time - (music.resolution * GRACE_NOTE_FORWARD_SHIFT_CONSTANT)) # no grace notes on the first note, to avoid negative times

        # ensure note time is an integer
        note.time = int(note.time) # ensure note time is an integer

        # add note to instrument
        instrument.notes.append(to_pretty_midi_note(note = note, map_time = map_time))

    # return instrument
    return instrument


def to_pretty_midi(music: "Music", realize_annotations: bool = False) -> PrettyMIDI:
    """Return a Music object as a PrettyMIDI object.

    Tempo changes are not supported yet.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?

    Returns
    -------
    :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    Notes
    -----
    Tempo information will not be included in the output.

    """
    # ensure we are operating on a copy of the original music object
    music = deepcopy(music)

    # Create an PrettyMIDI instance
    midi = PrettyMIDI()

    # Compute tempos
    tempo_times, tempi = [0], [float(DEFAULT_TEMPO)]
    metrical_time = (not music.real_time)
    if metrical_time:
        for tempo in music.tempos:
            tempo_times.append(tempo.time)
            tempi.append(tempo.qpm)

    # other tempo changes, like tempo spanners and fermata
    all_notes = sum((track.notes for track in music.tracks), []) # all notes
    max_note_time = max((note.time for note in all_notes))
    all_annotations = music.annotations + sum((track.annotations for track in music.tracks), [])
    current_tempo_index = 0
    for annotation in all_annotations:

        # skip annotations out of the relevant time scope
        if annotation.time <= max_note_time:
            continue

        # ensure that values are valid
        annotation_type = annotation.annotation.__class__.__name__
        if hasattr(annotation.annotation, "subtype"): # make sure subtype field is not none
            if annotation.annotation.subtype is None:
                continue
            else:
                annotation.annotation.subtype = clean_up_subtype(subtype = annotation.annotation.subtype) # clean up the subtype

        # update current_tempo_index if necessary; if real time, temporal features have already been accounted for
        if metrical_time:

            if current_tempo_index < (len(tempo_times) - 1): # avoid index error later on at last element in tempo_times
                if tempo_times[current_tempo_index + 1] <= annotation.time: # update current_tempo_index if necessary
                    current_tempo_index += 1 # increment

            # Fermata and fermatas stored inside of Articulation
            if (annotation_type == "Fermata") or (annotation_type == "Articulation"): # only apply when metrical time in use
                if (annotation_type == "Articulation") and ("fermata" not in annotation.annotation.subtype): # looking for fermatas hidden as articulations
                    continue # if not a fermata-articulation, skip
                longest_note_duration_at_current_time = max([note.duration for note in all_notes if note.time == annotation.time] + [0]) # go through notes and find longest duration note at the time of the fermata
                if longest_note_duration_at_current_time > 0:
                    tempo_times.insert(current_tempo_index + 1, annotation.time) # start of fermata time
                    tempi.insert(current_tempo_index + 1, tempi[current_tempo_index] * FERMATA_TEMPO_SLOWDOWN) # start of fermata tempo
                    tempo_times.insert(current_tempo_index + 2, annotation.time + longest_note_duration_at_current_time) # end of fermata time
                    tempi.insert(current_tempo_index + 2, tempi[current_tempo_index]) # end of fermata tempo
                    current_tempo_index += 2
                del longest_note_duration_at_current_time

            # TempoSpanner
            elif annotation_type == "TempoSpanner": # only apply when metrical time in use
                if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("lent", "rall", "rit", "smorz", "sost", "allarg"))): # slow-downs; lentando, rallentando, ritardando, smorzando, sostenuto, allargando
                    tempo_change_factor_fn = lambda t: t
                elif any((annotation.annotation.subtype.startswith(prefix) for prefix in ("accel", "leg"))): # speed-ups; accelerando, leggiero
                    tempo_change_factor_fn = lambda t: 1 / t
                else: # unknown TempoSpanner subtype
                    tempo_change_factor_fn = lambda t: 1
                spanner_passes_tempo_change = ((current_tempo_index < (len(tempi) - 1)) and ((annotation.time + annotation.annotation.duration) > tempo_times[current_tempo_index + 1]))
                post_spanner_tempo = tempi[current_tempo_index + int(spanner_passes_tempo_change)]
                if spanner_passes_tempo_change:
                    del tempo_times[current_tempo_index + 1], tempi[current_tempo_index + 1]
                for time, tempo_change_factor_magnitude in zip(range(annotation.time, annotation.time + annotation.annotation.duration, int(annotation.annotation.duration / N_TEMPO_SPANNER_SUBDIVISIONS)), range(1, 1 + N_TEMPO_SPANNER_SUBDIVISIONS)):
                    tempo_times.insert(current_tempo_index + tempo_change_factor_magnitude, time) # start of time
                    tempi.insert(current_tempo_index + tempo_change_factor_magnitude, int(tempi[current_tempo_index] * tempo_change_factor_fn(t = tempo_change_factor_magnitude))) # start of tempo
                current_tempo_index += N_TEMPO_SPANNER_SUBDIVISIONS + 1
                tempo_times.insert(current_tempo_index, annotation.time + annotation.annotation.duration) # start of fermata time
                tempi.insert(current_tempo_index, post_spanner_tempo) # start of fermata tempo
                del time, tempo_change_factor_magnitude, tempo_change_factor_fn, spanner_passes_tempo_change, post_spanner_tempo

    # clear up memory
    del current_tempo_index

    # Remove unnecessary tempo changes to speed up the search
    if len(tempi) > 1:
        last_tempo = tempi[0]
        last_time = tempo_times[0]
        i = 1
        while i < len(tempo_times):
            if tempi[i] == last_tempo:
                del tempo_times[i]
                del tempi[i]
            elif tempo_times[i] == last_time:
                del tempo_times[i - 1]
                del tempi[i - 1]
            else:
                last_tempo = tempi[i]
                i += 1

    if len(tempi) == 1:

        def map_time(time):
            return time * 60.0 / (music.resolution * tempi[0])

    else:
        tempo_times_np = np.array(tempo_times)
        tempi_np = np.array(tempi)

        # Compute the tempo time in absolute timing of each tempo change
        tempo_real_times = np.cumsum(
            np.diff(tempo_times_np) * 60.0 / (music.resolution * tempi_np[:-1])
        ).tolist()
        tempo_real_times.insert(0, 0.0)

        def map_time(time):
            idx = np.searchsorted(tempo_times_np, time, side="right") - 1
            residual = time - tempo_times_np[idx]
            factor = 60.0 / (music.resolution * tempi_np[idx])
            return tempo_real_times[idx] + residual * factor

    # Key signatures
    for key_signature in music.key_signatures:
        pm_key_signature = to_pretty_midi_key_signature(key_signature = key_signature, map_time = map_time)
        if pm_key_signature is not None:
            midi.key_signature_changes.append(pm_key_signature)

    # Time signatures
    for time_signature in music.time_signatures:
        midi.time_signature_changes.append(to_pretty_midi_time_signature(time_signature = time_signature, map_time = map_time))

    # Lyrics
    for lyric in music.lyrics:
        midi.lyrics.append(to_pretty_midi_lyric(lyric = lyric, map_time = map_time))

    # Text
    for annotation in all_annotations:
        if annotation.annotation.__class__.__name__ in ("Text", "TextSpanner", "RehearsalMark"):
            midi.text_events.append(to_pretty_midi_text(annotation = annotation, map_time = map_time))

    # Tracks
    for track in music.tracks:
        midi.instruments.append(to_pretty_midi_instrument(track = track, music = music, map_time = map_time, realize_annotations = realize_annotations))

    return midi


def write_midi_pretty_midi(path: Union[str, Path], music: "Music", realize_annotations: bool = False):
    """Write a Music object to a MIDI file using pretty_midi as backend.

    Tempo changes are not supported yet.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music` object
        Music object to convert.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?

    Notes
    -----
    Tempo information will not be included in the output.

    """
    midi = to_pretty_midi(music = music, realize_annotations = realize_annotations)
    midi.write(str(path))


def write_midi(
    path: Union[str, Path],
    music: "Music",
    realize_annotations: bool = False,
    backend: str = "mido",
    **kwargs: Any,
):
    """Write a Music object to a MIDI file.

    Parameters
    ----------
    path : str or Path
        Path to write the MIDI file.
    music : :class:`muspy.Music`
        Music object to write.
    realize_annotations : bool, default: False
        Should annotations be applied to loudness/timing of notes?
    backend: {'mido', 'pretty_midi'}, default: 'mido'
        Backend to use. Note that if `realize_annotations` is True,
        then the 'mido' backend is used, since the
        `realize_annotations` is better optimized for the 'mido'
        backend. However, the 'pretty_midi' backend has limited
        support for annotation realization.

    See Also
    --------
    write_midi_mido :
        Write a Music object to a MIDI file using mido as backend.
    write_midi_pretty_midi :
        Write a Music object to a MIDI file using pretty_midi as
        backend.

    """
    if backend == "mido" or realize_annotations:
        return write_midi_mido(path = path, music = music, realize_annotations = realize_annotations, **kwargs)
    elif backend == "pretty_midi":
        return write_midi_pretty_midi(path = path, music = music, realize_annotations = realize_annotations)
    else:
        raise ValueError("`backend` must by one of 'mido' and 'pretty_midi'.")


def to_miditoolkit_tempo(tempo: Tempo) -> Optional[MtkTempo]:
    """Return a Tempo object as a miditoolkit TempoChange."""
    return MtkTempo(tempo=tempo.qpm, time=tempo.time)


def to_miditoolkit_key_signature(
    key_signature: KeySignature,
) -> Optional[MtkKeySignature]:
    """Return a KeySignature object as a miditoolkit KeySignature."""
    # TODO: `key_signature.root_str` might be given
    if key_signature.root is None:
        return None
    if key_signature.mode not in ("major", "minor"):
        return None
    suffix = "m" if key_signature.mode == "minor" else ""
    return MtkKeySignature(
        key_name=PITCH_NAMES[key_signature.root] + suffix,
        time=key_signature.time,
    )


def to_miditoolkit_time_signature(
    time_signature: TimeSignature,
) -> MtkTimeSignature:
    """Return a TimeSignature object as a miditoolkit TimeSignature."""
    return MtkTimeSignature(
        numerator=time_signature.numerator,
        denominator=time_signature.denominator,
        time=time_signature.time,
    )


def to_miditoolkit_lyric(lyric: Lyric) -> MtkLyric:
    """Return a Lyric object as a miditoolkit Lyric object."""
    return MtkLyric(text=lyric.lyric, time=lyric.time)


def to_miditoolkit_note(note: Note) -> MtkNote:
    """Return a Note object as a miditoolkit Note object."""
    velocity = note.velocity if note.velocity is not None else DEFAULT_VELOCITY
    return MtkNote(
        velocity=velocity, pitch=note.pitch, start=note.time, end=note.end
    )


def to_miditoolkit_instrument(track: Track) -> MtkInstrument:
    """Return a Track object as a miditoolkit Instrument object."""
    instrument = MtkInstrument(
        program=track.program, is_drum=track.is_drum, name=track.name
    )
    for note in track.notes:
        instrument.notes.append(to_miditoolkit_note(note))
    return instrument


def to_miditoolkit(music: "Music") -> MtkMidiFile:
    """Return a Music object as a miditoolkit object.

    Tempo changes are not supported yet.

    Parameters
    ----------
    music : :class:`muspy.Music` object
        Music object to convert.

    Returns
    -------
    :class:`pretty_midi.PrettyMIDI`
        Converted PrettyMIDI object.

    Notes
    -----
    Tempo information will not be included in the output.

    """
    # Create an PrettyMIDI instance
    midi = MtkMidiFile(ticks_per_beat=music.resolution)

    # Tempos
    for tempo in music.tempos:
        midi.tempo_changes.append(to_miditoolkit_tempo(tempo))

    # Key signatures
    for key_signature in music.key_signatures:
        mtk_key_signature = to_miditoolkit_key_signature(key_signature)
        if mtk_key_signature is not None:
            midi.key_signature_changes.append(mtk_key_signature)

    # Time signatures
    for time_signature in music.time_signatures:
        midi.time_signature_changes.append(
            to_miditoolkit_time_signature(time_signature)
        )

    # Lyrics
    for lyric in music.lyrics:
        midi.lyrics.append(to_miditoolkit_lyric(lyric))

    # Tracks
    for track in music.tracks:
        midi.instruments.append(to_miditoolkit_instrument(track))

    # Compute max tick
    midi.max_tick = music.get_end_time()

    return midi
