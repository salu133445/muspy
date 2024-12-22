"""MusicXML output interface."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Union, Tuple
import xml.etree.ElementTree as ET

from music21.musicxml.archiveTools import compressXML
from music21.instrument import instrumentFromMidiProgram
from music21.interval import Interval

from .music21 import to_music21, PITCH_NAMES
from .midi import DRUM_CHANNEL

if TYPE_CHECKING:
    from ..music import Music

DRUMSET_INSTRUMENTS = [
    ("Acoustic Bass Drum", 36),
    ("Bass Drum 1", 37),
    ("Side Stick", 38),
    ("Acoustic Snare", 39),
    ("Hand Clap", 40),
    ("Electric Snare", 41),
    ("Low Floor Tom", 42),
    ("Closed Hi Hat", 43),
    ("High Floor Tom", 44),
    ("Pedal Hi-Hat", 45),
    ("Low Tom", 46),
    ("Open Hi-Hat", 47),
    ("Low-Mid Tom", 48),
    ("Hi Mid Tom", 49),
    ("Crash Cymbal 1", 50),
    ("High Tom", 51),
    ("Ride Cymbal 1", 52),
    ("Chinese Cymbal", 53),
    ("Ride Bell", 54),
    ("Tambourine", 55),
    ("Splash Cymbal", 56),
    ("Cowbell", 57),
    ("Crash Cymbal 2", 58),
    ("Vibraslap", 59),
    ("Ride Cymbal 2", 60),
    ("Hi Bongo", 61),
    ("Low Bongo", 62),
    ("Mute Hi Conga", 63),
    ("Open Hi Conga", 64),
    ("Low Conga", 65),
    ("High Timbale", 66),
    ("Low Timbale", 67),
    ("High Agogo", 68),
    ("Low Agogo", 69),
    ("Cabasa", 70),
    ("Maracas", 71),
    ("Short Whistle", 72),
    ("Long Whistle", 73),
    ("Short Guiro", 74),
    ("Long Guiro", 75),
    ("Claves", 76),
    ("Hi Wood Block", 77),
    ("Low Wood Block", 78),
    ("Mute Cuica", 79),
    ("Open Cuica", 80),
    ("Mute Triangle", 81),
    ("Open Triangle", 82),
]


def get_transpose_element(transposition: Interval = None) -> ET.Element:
    """Return the XML Element object that represents the transpose information for the given transposition."""

    # get information about the transposition (chromatic, diatonic, octave)
    genericSteps = transposition.diatonic.generic.directed if transposition is not None else 1
    musicxmlOctaveShift, musicxmlDiatonic = divmod(abs(genericSteps) - 1, 7)
    musicxmlChromatic = abs(transposition.chromatic.semitones) % 12 if transposition is not None else 0
    if genericSteps < 0:
        musicxmlDiatonic *= -1
        musicxmlOctaveShift *= -1
        musicxmlChromatic *= -1

    # create MusicXML elements
    mxTranspose = ET.Element("transpose")
    mxDiatonic = ET.SubElement(mxTranspose, "diatonic") # diatonic shift
    mxDiatonic.text = str(musicxmlDiatonic)
    mxChromatic = ET.SubElement(mxTranspose, "chromatic") # chromatic shift
    mxChromatic.text = str(musicxmlChromatic)
    if musicxmlOctaveShift != 0: # if there is an octave shift
        mxOctaveChange = ET.SubElement(mxTranspose, "octave-change")
        mxOctaveChange.text = str(musicxmlOctaveShift)

    # return element
    return mxTranspose


def get_instrument_elements(instrument_name: str, percussion_map_pitch: int, part_id: str) -> Tuple[ET.Element, ET.Element]:
    """Return two XML elements, representing the score-instrument and midi-instrument elements for a given instrument."""

    # get the instrument id
    instrument_id = f"{part_id}-T{percussion_map_pitch}"

    # create score instrument
    score_instrument = ET.Element("score-instrument", id = instrument_id)
    instrument_name_element = ET.SubElement(score_instrument, "instrument-name")
    instrument_name_element.text = instrument_name

    # create midi instrument
    midi_instrument = ET.Element("midi-instrument", id = instrument_id)
    midi_channel = ET.SubElement(midi_instrument, "midi-channel")
    midi_channel.text = str(DRUM_CHANNEL) # set to the drum channel
    midi_program = ET.SubElement(midi_instrument, "midi-program")
    midi_program.text = "1" # default
    midi_unpitched = ET.SubElement(midi_instrument, "midi-unpitched")
    midi_unpitched.text = str(percussion_map_pitch) # midi pitch that maps to this instrument
    midi_volume = ET.SubElement(midi_instrument, "volume")
    midi_volume.text = "78.7402" # MuseScore default
    midi_pan = ET.SubElement(midi_instrument, "pan")
    midi_pan.text = "0" # no pan of the instrument

    # return the score and midi instrument elements
    return score_instrument, midi_instrument


def get_unpitched_and_instrument_elements(note: ET.Element, part_id: str) -> Tuple[ET.Element, ET.Element]:
    """
    Return two XML elements, the unpitched element of a pitched drum note,
    and the instrument element associated with the new unpitched drum note.
    """

    # get info about pitch
    pitch_element = note.find(path = "pitch")
    pitch_step = pitch_element.find(path = "step").text
    pitch_octave = int(pitch_element.find(path = "octave").text)
    pitch_alter = pitch_element.find(path = "alter")
    pitch_alter = int(0 if pitch_alter is None else pitch_alter.text)

    # reconstruct midi pitch from the pitch information gathered in previous step
    percussion_map_pitch = PITCH_NAMES.index(pitch_step) + (12 * (pitch_octave + 1)) + pitch_alter + 1

    # remove any pitch-related elements from note
    note.remove(pitch_element)
    accidental_element = note.find(path = "accidental")
    if accidental_element is not None:
        note.remove(accidental_element)

    # create unpitched XML element
    unpitched = ET.Element("unpitched")
    display_step = ET.SubElement(unpitched, "display-step")
    display_step.text = pitch_step
    display_octave = ET.SubElement(unpitched, "display-octave")
    display_octave.text = str(pitch_octave)

    # create note instrument element
    note_instrument = ET.Element("instrument", id = f"{part_id}-T{percussion_map_pitch}")

    # return elements
    return unpitched, note_instrument


def write_musicxml(
    path: Union[str, Path], music: "Music", compressed: bool = None
):
    """Write a Music object to a MusicXML file.

    Parameters
    ----------
    path : str or Path
        Path to write the MusicXML file.
    music : :class:`muspy.Music`
        Music object to write.
    compressed : bool, optional
        Whether to write to a compressed MusicXML file. If None, infer
        from the extension of the filename ('.xml' and '.musicxml' for
        an uncompressed file, '.mxl' for a compressed file).

    """

    # ensure path is a string
    path = str(path)

    # make sure music is not in real time
    if music.real_time:
        raise RuntimeError("Cannot write to MusicXML when `music` is in real time (`music.real_time` == True).")

    # get music as a music21 score
    score = to_music21(music = music)

    # write as xml temporarily, correct some of music21's mistakes
    path_temp = f"{path}.temp.xml"
    score.write(fmt = "xml", fp = path_temp)
    root = ET.parse(path_temp).getroot()

    # make sure transpositions are present in XML file
    for i, elem in enumerate(root.findall(path = "part")):
        first_measure = elem.find(path = "measure")
        transposition = instrumentFromMidiProgram(number = music.tracks[i].program).transposition # get the transposition
        if transposition is not None and first_measure.find(path = "attributes/transpose") is None:
            attributes = first_measure.find(path = "attributes")
            if attributes is None:
                attributes = ET.Element("attributes")
                first_measure.insert(0, attributes)
            attributes.append(get_transpose_element(transposition = transposition))

    # get indicies of drum tracks
    drum_track_indicies = set(filter(lambda i: music.tracks[i].is_drum, range(len(music.tracks))))

    # make sure drum midi instruments are written correctly in the part list
    for i, elem in enumerate(root.findall(path = "part-list/score-part")):
        if i not in drum_track_indicies: # skip over non-drum tracks
            continue
        elem.remove(elem.find(path = "part-abbreviation"))
        elem.remove(elem.find(path = "score-instrument"))
        elem.remove(elem.find(path = "midi-instrument"))
        midi_instruments = []
        for instrument_name, percussion_map_pitch in DRUMSET_INSTRUMENTS:
            score_instrument, midi_instrument = get_instrument_elements(instrument_name = instrument_name, percussion_map_pitch = percussion_map_pitch, part_id = elem.get("id"))
            elem.append(score_instrument)
            midi_instruments.append(midi_instrument)
        elem.append(ET.Element("midi-device", port = "1"))
        for midi_instrument in midi_instruments:
            elem.append(midi_instrument)

    # make sure to update pitched drum notes to unpitched
    for i, elem in enumerate(root.findall(path = "part")):
        if i not in drum_track_indicies: # skip over non-drum tracks
            continue
        for note in elem.findall(path = "measure/note"):
            if note.find(path = "rest") is not None: # skip over rests
                continue
            unpitched, note_instrument = get_unpitched_and_instrument_elements(note = note, part_id = elem.get("id"))
            unpitched_position = int(note.find(path = "chord") is not None)
            note.insert(unpitched_position, unpitched)
            note.insert(unpitched_position + 2, note_instrument)

    # infer compression
    if compressed is None:
        if path.endswith((".xml", ".musicxml")):
            compressed = False
        elif path.endswith(".mxl"):
            compressed = True
        else:
            raise ValueError("Cannot infer file type from the extension.")

    # compress the file (or not)
    tree = ET.ElementTree(root)
    # ET.indent(tree, space = "\t", level = 0)
    tree.write(path_temp)
    if compressed:
        compressXML(filename = path_temp, deleteOriginal = True)
        os.rename(src = f"{path}.temp.mxl", dst = path)
    else: # don't compress
        os.rename(src = path_temp, dst = path)
