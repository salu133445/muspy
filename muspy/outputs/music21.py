"""Music21 converter interface."""
from typing import TYPE_CHECKING, Tuple, Dict, List
from warnings import warn
from fractions import Fraction
from itertools import groupby
from re import sub
from copy import deepcopy

from music21.metadata import Contributor, Copyright
from music21.metadata import Metadata as M21MetaData
from music21.meter import TimeSignature as M21TimeSignature
from music21.key import KeySignature as M21KeySignature
from music21.note import Note as M21Note, noteheadTypeNames
from music21.stream import Part, Score
from music21.exceptions21 import StreamException
from music21.duration import Duration
from music21.clef import PercussionClef
from music21.instrument import instrumentFromMidiProgram
from music21.chord import Chord as M21Chord
from music21.harmony import ChordSymbol as M21ChordSymbol
from music21 import tempo as M21Tempo
from music21 import articulations as M21Articulation
from music21 import expressions as M21Expression
from music21 import spanner as M21Spanner
from music21 import dynamics as M21Dynamic
import music21.musicxml.archiveTools
import music21.beam

from ..classes import Metadata, Annotation
from .midi import PITCH_NAMES, DRUM_CHANNEL, clean_up_subtype

if TYPE_CHECKING:
    from ..music import Music

# silence weird warnings from music21
def noop(input):
    pass
music21.musicxml.archiveTools.environLocal.warn = noop
music21.beam.environLocal.warn = noop


def get_octave_from_pitch(pitch: int) -> int:
    """Given the MIDI pitch number, return the octave of that note."""
    return (pitch // 12) - 1


def convert_chromatic_to_circle_of_fifths_steps(transpose_chromatic: int = 0) -> int:
    """
    Given a number of semitones to transpose, return the necessary number of steps to
    make the same transposition on the circle of fifths.
    """
    transpose_chromatic = transpose_chromatic % -12 # get in range 0 through 12
    if (-transpose_chromatic % 2 == 0):
        return transpose_chromatic
    else:
        return (transpose_chromatic + 6) % -12


def to_music21_metadata(metadata: Metadata) -> M21MetaData:
    """Return a Metadata object as a music21 Metadata object.

    Parameters
    ----------
    metadata : :class:`muspy.Metadata`
        Metadata object to convert.

    Returns
    -------
    `music21.metadata.Metadata`
        Converted music21 Metadata object.

    """
    meta = M21MetaData()

    # Title is usually stored in movement-title. See
    # https://www.musicxml.com/tutorial/file-structure/score-header-entity/
    if metadata.title:
        meta.movementName = metadata.title

    if metadata.copyright:
        meta.copyright = Copyright(metadata.copyright)
    for creator in metadata.creators:
        meta.addContributor(Contributor(name=creator))
    return meta


def to_music21(music: "Music") -> Score:
    """Return a Music object as a music21 Score object.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to convert.

    Returns
    -------
    `music21.stream.Score`
        Converted music21 Score object.

    """

    # so that we do not operate on the original music object
    music = deepcopy(music)

    # make sure music is not in real time
    if music.real_time:
        raise RuntimeError("Cannot convert to music21 when `music` is in real time (`music.real_time` == True).")

    # create a new score
    score = Score()

    # helper functions
    get_offset = lambda time: time / music.resolution
    def get_duration(duration: int) -> Duration:
        """
        Helper function to get the duration of something, returning a music21 Duration object.
        Make sure the duration is valid so no bugs are thrown.
        """
        m21_duration = Duration(quarterLength = Fraction(duration, music.resolution))
        if any((tup.durationNormal.quarterLength <= (1 / (2 ** 9)) for tup in m21_duration.tuplets)): # check for invalid durations
            return Duration(quarterLength = 0)
        else:
            return m21_duration
    get_time_from_offset = lambda offset: offset * music.resolution

    # metadata
    if music.metadata is not None:
        score.metadata = to_music21_metadata(metadata = music.metadata)

    # tracks
    for i, track in enumerate(music.tracks):

        # create a new part
        part = Part()
        part.partName = track.name
        part_id = f"P{i + 1}"

        # set instrument
        if track.is_drum:
            part.clef = PercussionClef()
            channel = DRUM_CHANNEL
        else:
            channel = i % 15 # .mid has 15 channels for instruments other than drums
            channel += int(channel >= DRUM_CHANNEL) # avoid drum channel by adding one if the channel is greater than 8
        instrument = instrumentFromMidiProgram(number = track.program)
        instrument.partId = part_id
        instrument.partName = track.name
        instrument.instrumentId = f"{part_id}-T1"
        instrument.instrumentName = track.name
        instrument.midiChannel = channel
        part.append(instrument)

        # amount to adjust tone
        part.atSoundingPitch = False
        transpose_chromatic = instrument.transposition.chromatic.semitones if instrument.transposition is not None else 0
        def get_note_str_and_octave(pitch: int, pitch_str: str) -> Tuple[str, int]:
            """Helper function for extracting the note's string and octave for music21."""
            if pitch_str is None:
                pitch_str = PITCH_NAMES[pitch % len(PITCH_NAMES)]
            n_accidentals = pitch_str[1:].count("#") - pitch_str[1:].count("b")
            note_str = PITCH_NAMES[(PITCH_NAMES.index(pitch_str[0]) + n_accidentals - transpose_chromatic) % len(PITCH_NAMES)].replace("b", "-")
            note_octave = get_octave_from_pitch(pitch = pitch - transpose_chromatic) # adjust pitch for tuning of instrument
            return note_str, note_octave

        # add tempos
        for tempo in music.tempos: # loop through tempos
            if tempo.text is None or tempo.text.startswith("<sym>"): # bpm is explicitly supplied in text or not supplied at all
                m21_tempo = M21Tempo.MetronomeMark(number = tempo.qpm) # create tempo marking with bpm
            else: # bpm is implied by tempo name
                m21_tempo = M21Tempo.MetronomeMark(text = tempo.text, numberSounding = tempo.qpm) # create tempo marking with text
            m21_tempo.offset = get_offset(time = tempo.time) # define offset
            part.insert(offsetOrItemOrList = m21_tempo.offset, itemOrNone = m21_tempo)

        # add time signatures
        for time_signature in music.time_signatures: # loop through time signatures
            if (time_signature.numerator is None) or (time_signature.denominator is None):
                continue
            m21_time_signature = M21TimeSignature(value = f"{time_signature.numerator}/{time_signature.denominator}") # instantiate time signature object
            m21_time_signature.offset = get_offset(time = time_signature.time) # define offset
            part.insert(offsetOrItemOrList = m21_time_signature.offset, itemOrNone = m21_time_signature)

        # add key signatures
        for key_signature in music.key_signatures: # loop through key signatures
            m21_key_signature = M21KeySignature(sharps = (key_signature.fifths - convert_chromatic_to_circle_of_fifths_steps(transpose_chromatic = transpose_chromatic)) if key_signature.fifths is not None else 0) # create key object
            m21_key_signature = m21_key_signature.asKey(mode = key_signature.mode.lower() if key_signature.mode is not None else "major")
            m21_key_signature.offset = get_offset(time = key_signature.time) # define offset
            part.insert(offsetOrItemOrList = m21_key_signature.offset, itemOrNone = m21_key_signature)

        # add notes to part (and grace notes, lyrics, noteheads, and articulations)
        lyrics: Dict[int, str] = {lyric.time: lyric.lyric for lyric in track.lyrics} # put lyrics into dictionary (where keys are the time)
        # chords: Dict[Tuple[int, int, bool], list] = dict()

        # loop through notes
        note_notations = [] # store any note notations as annotations
        for note in track.notes:

            # create M21 Note object
            note_str, note_octave = get_note_str_and_octave(pitch = note.pitch, pitch_str = note.pitch_str)
            m21_note = M21Note(name = note_str, octave = note_octave) # create note object

            # check if grace note
            if note.is_grace: # check if grace note
                m21_note.type = "eighth" # so it looks like a normal grace note with a flag
                m21_note = m21_note.getGrace() # convert to grace note
            # if the note is a normal note
            else:
                m21_note.duration = get_duration(duration = note.duration)
                if m21_note.duration.type == "zero": # ignore notes with invalid durations
                    continue
                # check if there is a lyric at that note
                if note.time in lyrics.keys():
                    m21_note.lyric = lyrics[note.time] # add lyric

            # check if there are any relevant notations
            if note.notations is not None:

                # add notations to note_notations
                note_notations.extend([Annotation(time = note.time, annotation = notation) for notation in note.notations])

                # check if there is a notehead at that note
                note_noteheads = list(map(
                    lambda notehead: notehead.subtype.lower(),
                    filter(lambda notation: notation.__class__.__name__ == "Notehead", note.notations)
                ))
                if len(note_noteheads) > 0 and note_noteheads[0] in noteheadTypeNames: # check if notehead is a valid notehead for music21
                    m21_note.notehead = note_noteheads[0] # add notehead
                del note_noteheads

                # check if there is an articulation(s) at that note
                note_articulations = list(map(
                    lambda articulation: clean_up_subtype(subtype = articulation.subtype),
                    filter(lambda notation: notation.__class__.__name__ == "Articulation" or notation.__class__.__name__ == "Symbol", note.notations)
                ))
                for articulation in note_articulations:
                    if articulation is None:
                        continue
                    if "accent" in articulation:
                        m21_note.articulations.append(M21Articulation.Accent())
                    if "staccato" in articulation:
                        m21_note.articulations.append(M21Articulation.Staccato())
                    if "staccatissimo" in articulation:
                        m21_note.articulations.append(M21Articulation.Staccatissimo())
                    if "tenuto" in articulation:
                        m21_note.articulations.append(M21Articulation.Tenuto())
                    if "pizzicato" in articulation:
                        if "snap" in articulation:
                            m21_note.articulations.append(M21Articulation.SnapPizzicato())
                        elif "nail" in articulation:
                            m21_note.articulations.append(M21Articulation.NailPizzicato())
                        else: # normal pizzicato is default
                            m21_note.articulations.append(M21Articulation.Pizzicato())
                    if "spiccato" in articulation:
                        m21_note.articulations.append(M21Articulation.Spiccato())
                    if "bow" in articulation:
                        if "up" in articulation:
                            m21_note.articulations.append(M21Articulation.UpBow())
                        else: # down is default
                            m21_note.articulations.append(M21Articulation.DownBow())
                    if any((keyword in articulation for keyword in ("mute", "close"))): # brass mute
                        m21_note.articulations.append(M21Articulation.BrassIndication(name = "muted"))
                    if any((keyword in articulation for keyword in ("open", "ouvert"))): # open
                        if "string" in articulation:
                            m21_note.articulations.append(M21Articulation.OpenString())
                        else: # defaults to brass open mute
                            m21_note.articulations.append(M21Articulation.BrassIndication(name = "open"))
                    if "doit" in articulation:
                        m21_note.articulations.append(M21Articulation.Doit())
                    if "fall" in articulation:
                        m21_note.articulations.append(M21Articulation.Falloff())
                    if "plop" in articulation:
                        m21_note.articulations.append(M21Articulation.Plop())
                    if "scoop" in articulation:
                        m21_note.articulations.append(M21Articulation.Scoop())
                    if "harmonic" in articulation:
                        m21_note.articulations.append(M21Articulation.Harmonic())
                    if "stopped" in articulation:
                        m21_note.articulations.append(M21Articulation.Stopped())
                    if "stress" in articulation:
                        m21_note.articulations.append(M21Articulation.Stress())
                    if "unstress" in articulation:
                        m21_note.articulations.append(M21Articulation.Unstress())
                del note_articulations

            # add note to chords
            # chord_descriptor_tuple = (note.time, note.duration, note.is_grace)
            # if chord_descriptor_tuple not in chords.keys():
            #     chords[chord_descriptor_tuple] = []
            # chords[chord_descriptor_tuple].append(m21_note)

            # add note to part
            m21_note.offset = get_offset(time = note.time)
            part.insert(offsetOrItemOrList = m21_note.offset, itemOrNone = m21_note)

        # add chords to part
        # for chord_descriptor_tuple, chord_notes in chords.items():
        #     m21_chord = M21Chord(notes = chord_notes)
        #     m21_chord.offset = get_offset(time = chord_descriptor_tuple[0])
        #     part.insert(offsetOrItemOrList = m21_chord.offset, itemOrNone = m21_chord)
        # del chords # clean up some memory

        # clean up some memory
        del lyrics

        # add expressive features to part
        for annotation in sorted(music.annotations + track.annotations + note_notations, key = lambda annotation: annotation.time):

            # clean up subtype if necessary
            if hasattr(annotation.annotation, "subtype"):
                if annotation.annotation.subtype is None:
                    continue
                else:
                    annotation.annotation.subtype = clean_up_subtype(subtype = annotation.annotation.subtype) # clean up the subtype

            # some boolean flags
            annotation_type = annotation.annotation.__class__.__name__
            is_fermata = (annotation_type == "Fermata") # fermata
            if any((annotation_type == keyword for keyword in ("Articulation", "Symbol"))): # instance where fermatas are hidden as articulations
                is_fermata = "fermata" in annotation.annotation.subtype.lower()

            # Text, TextSpanner
            if any((annotation_type == keyword for keyword in ("Text", "TextSpanner"))):
                m21_annotation = M21Expression.TextExpression(content = annotation.annotation.text)
                if annotation_type == "TextSpanner": # text spanners
                    m21_annotation.duration = get_duration(duration = annotation.annotation.duration)
                    if m21_annotation.duration.type == "zero": # ignore notes with invalid durations
                        continue

            # RehearsalMark
            elif annotation_type == "RehearsalMark":
                m21_annotation = M21Expression.RehearsalMark(content = annotation.annotation.text)

            # Dynamic
            elif annotation_type == "Dynamic":
                m21_annotation = M21Dynamic.Dynamic(value = annotation.annotation.subtype)

            # Chord Symbol
            elif annotation_type == "ChordSymbol":
                try:
                    m21_annotation = M21ChordSymbol(annotation.annotation.root_str.replace("b", "-") + (annotation.annotation.name.lower() if annotation.annotation.name else ""))
                except (ValueError): # not all chords are supported, so we do our best, and ignore unknown chord symbols
                    continue

            # Fermata
            elif is_fermata:
                m21_annotation = M21Expression.Fermata()

            # Ornament, Articulation, Symbol, TechAnnotation
            elif any((annotation_type == keyword for keyword in ("Ornament", "Articulation", "Symbol", "TechAnnotation"))):
                if annotation_type == "TechAnnotation": # just to make things easier
                    annotation.annotation.subtype = annotation.annotation.tech_type if annotation.annotation.tech_type is not None else annotation.annotation.text # add subtype field to techannotation
                annotation.annotation.subtype = clean_up_subtype(subtype = annotation.annotation.subtype) # clean up the subtype for tech annotation
                if "mordent" in annotation.annotation.subtype: # mordent
                    if any((keyword in annotation.annotation.subtype for keyword in ("reverse", "invert"))):
                        m21_annotation = M21Expression.InvertedMordent()
                    else: # default is normal
                        m21_annotation = M21Expression.Mordent()
                elif "trill" in annotation.annotation.subtype: # trill
                    if any((keyword in annotation.annotation.subtype for keyword in ("reverse", "invert"))):
                        m21_annotation = M21Expression.InvertedTrill()
                    else: # default is normal
                        m21_annotation = M21Expression.Trill()
                elif "schleifer" in annotation.annotation.subtype: # schleifer
                    m21_annotation = M21Expression.Schleifer()
                elif "shake" in annotation.annotation.subtype: # shake
                    m21_annotation = M21Expression.Shake()
                elif "tremolo" in annotation.annotation.subtype: # tremolo
                    m21_annotation = M21Expression.Tremolo()
                elif "turn" in annotation.annotation.subtype: # turn
                    if "reverse" in annotation.annotation.subtype:
                        m21_annotation = M21Expression.InvertedTurn()
                    else: # default is normal turn
                        m21_annotation = M21Expression.Turn()
                else: # unknown ornament or articulation
                    continue

            # TrillSpanner, HairPinSpanner, SlurSpanner, GlissandoSpanner, OttavaSpanner, TrillSpanner; anything that spans multiple notes
            elif any((annotation_type == keyword for keyword in ("TrillSpanner", "HairPinSpanner", "SlurSpanner", "GlissandoSpanner", "OttavaSpanner", "TrillSpanner"))):
                spanned_notes = list(filter(lambda note: get_time_from_offset(offset = note.offset) >= annotation.time and get_time_from_offset(offset = note.offset) <= (annotation.time + annotation.annotation.duration), part.getElementsByClass(M21Note)))
                # TempoSpanner
                if annotation_type == "TempoSpanner":
                    if any((annotation.annotation.subtype.startswith(prefix) for prefix in ("accel", "leg"))): # speed-ups; accelerando, leggiero
                        m21_annotation = M21Tempo.AccelerandoSpanner(*spanned_notes)
                    else: # slow-downs; lentando, rallentando, ritardando, smorzando, sostenuto, allargando, etc.; the default
                        m21_annotation = M21Tempo.RitardandoSpanner(*spanned_notes)
                # HairPinSpanner
                elif annotation_type == "HairPinSpanner":
                    if any((keyword in "".join(annotation.annotation.subtype.split("-")) for keyword in ("dim", "decres"))): # diminuendo
                        m21_annotation = M21Dynamic.Diminuendo(*spanned_notes)
                    else: # crescendo
                        m21_annotation = M21Dynamic.Crescendo(*spanned_notes)
                # SlurSpanner
                elif annotation_type == "SlurSpanner":
                    m21_annotation = M21Spanner.Slur(*spanned_notes)
                # GlissandoSpanner
                elif annotation_type == "GlissandoSpanner":
                    m21_annotation = M21Spanner.Glissando(*spanned_notes, lineType = "wavy" if annotation.annotation.is_wavy else "solid")
                # OttavaSpanner
                elif annotation_type == "OttavaSpanner":
                    try:
                        m21_annotation = M21Spanner.Ottava(type = annotation.annotation.subtype, transposing = False)
                    except (M21Spanner.SpannerException): # some unknown type of ottava
                        continue
                # TrillSpanner
                elif annotation_type == "TrillSpanner" and len(spanned_notes) >= 2:
                    m21_annotation = M21Expression.TrillExtension(spanned_notes[0], spanned_notes[1])
                # unknown spanner
                else:
                    continue

            # Arpeggio
            elif annotation_type == "Arpeggio":
                if annotation.annotation.subtype == "bracket":
                    arpeggio_type = "bracket"
                elif "up" in annotation.annotation.subtype:
                    arpeggio_type = "up"
                elif "down" in annotation.annotation.subtype:
                    arpeggio_type = "down"
                else:
                    arpeggio_type = "normal"
                m21_annotation = M21Expression.ArpeggioMark(arpeggioType = arpeggio_type)

            # Tremolo
            elif annotation_type == "Tremolo":
                number_of_marks = sub(pattern = "[^\d]", repl = "", string = annotation.annotation.subtype)
                m21_annotation = M21Expression.Tremolo(numberOfMarks = (int(number_of_marks) // 8) if len(number_of_marks) > 0 else 3)
                del number_of_marks

            # TremoloBar
            # elif annotation_type == "TremoloBar":
            #     pass # to be implemented on a later date

            # ChordLine
            # elif annotation_type == "ChordLine":
            #     pass # to be implemented on a later data

            # Bend
            # elif annotation_type == "Bend":
            #     pass # to be implemented on a later date

            # PedalSpanner
            # elif annotation_type == "PedalSpanner":
            #     pass # music21 does not have pedals

            # VibratoSpanner
            # elif annotation_type == "VibratoSpanner":
            #     pass # so rare that this is not worth implementing

            # if the annotation is unknown, skip it
            else:
                continue

            # insert annotation into part
            try:
                m21_annotation.offset = get_offset(time = annotation.time)
                part.insert(offsetOrItemOrList = m21_annotation.offset, itemOrNone = deepcopy(m21_annotation)) # as to avoid the StreamException object * is already found in this Stream
            except StreamException as stream_exception:
                warn(str(stream_exception), RuntimeWarning)

        # append the part to score
        score.append(part)

    # return the score
    return score
