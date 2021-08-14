"""MusicXML input interface."""
import xml.etree.ElementTree as ET
from collections import OrderedDict
from functools import reduce
from operator import attrgetter
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar, Union
from xml.etree.ElementTree import Element
from zipfile import ZipFile

from ..classes import (
    KeySignature,
    Lyric,
    Metadata,
    Note,
    Tempo,
    TimeSignature,
    Track,
)
from ..music import Music
from ..utils import CIRCLE_OF_FIFTHS, MODE_CENTERS, NOTE_MAP, NOTE_TYPE_MAP

T = TypeVar("T")


class MusicXMLError(Exception):
    """An error class for MusicXML related exceptions."""


def _gcd(a: int, b: int) -> int:
    """Return greatest common divisor using Euclid's Algorithm.

    Code copied from https://stackoverflow.com/a/147539.

    """
    while b:
        a, b = b, a % b
    return a


def _lcm_two_args(a: int, b: int) -> int:
    """Return least common multiple.

    Code copied from https://stackoverflow.com/a/147539.

    """
    return a * b // _gcd(a, b)


def _lcm(*args: int) -> int:
    """Return lcm of args.

    Code copied from https://stackoverflow.com/a/147539.

    """
    return reduce(_lcm_two_args, args)  # type: ignore


def _get_text(
    element: Element,
    path: str,
    default: T = None,
    remove_newlines: bool = False,
) -> Union[str, T]:
    """Return the text of the first matching element."""
    elem = element.find(path)
    if elem is not None and elem.text is not None:
        if remove_newlines:
            return " ".join(elem.text.splitlines())
        return elem.text
    return default  # type: ignore


def _get_required(element: Element, path: str) -> Element:
    """Return a required element; raise ValueError if not found."""
    elem = element.find(path)
    if elem is None:
        raise MusicXMLError("Element `{}` is required.".format(path))
    return elem


def _get_required_attr(element: Element, attr: str) -> str:
    """Return a required attribute; raise MusicXMLError if not found."""
    attribute = element.get(attr)
    if attribute is None:
        raise MusicXMLError("Attribute '{}' is required for an element ")
    return attribute


def _get_required_text(
    element: Element, path: str, remove_newlines: bool = False
) -> str:
    """Return a required text; raise MusicXMLError if not found."""
    elem = element.find(path)
    if elem is None:
        raise MusicXMLError(
            "Child element '{}' is required for an element '{}'."
            "".format(path, element.tag)
        )
    if elem.text is None:
        raise MusicXMLError(
            "Text content '{}' of an element '{}' must not be empty."
            "".format(path, element.tag)
        )
    if remove_newlines:
        return " ".join(elem.text.splitlines())
    return elem.text


def parse_metronome_elem(elem: Element) -> Optional[float]:
    """Return a qpm value parsed from a metronome element."""
    beat_unit = _get_text(elem, "beat-unit")
    if beat_unit is not None:
        per_minute = _get_text(elem, "per-minute")
        if per_minute is not None and beat_unit in NOTE_TYPE_MAP:
            qpm = NOTE_TYPE_MAP[beat_unit] * float(per_minute)
            if elem.find("beat-unit-dot") is not None:
                qpm *= 1.5
            return qpm
    return None


def parse_key_elem(elem: Element) -> Dict:
    """Return a dictionary with data parsed from a key element."""
    mode = _get_text(elem, "mode", "major")
    fifths = int(_get_required_text(elem, "fifths"))
    if mode is None:
        return {"fifths": fifths}
    idx = MODE_CENTERS[mode] + fifths
    if idx < 0 or idx > 20:
        return {"fifths": fifths, "mode": mode}
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + fifths]
    return {"root": root, "mode": mode, "fifths": fifths, "root_str": root_str}


def parse_pitch_elem(elem: Element) -> Tuple[int, str]:
    """Return a (pitch, pitch_str) tuple parsed from a pitch element."""
    step = _get_required_text(elem, "step")
    octave = int(_get_required_text(elem, "octave"))
    alter = int(_get_text(elem, "alter", 0))
    pitch = 12 * (octave + 1) + NOTE_MAP[step] + alter
    if alter > 0:
        pitch_str = step + "#" * alter + str(octave)
    elif alter < 0:
        pitch_str = step + "b" * (-alter) + str(octave)
    else:
        pitch_str = step + str(octave)
    return pitch, pitch_str


def parse_part_elem(
    part_elem: Element, resolution: int, instrument_info: dict
) -> dict:
    """Return a dictionary with data parsed from a part element."""
    # Initialize lists and placeholders
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    notes: Dict[str, List[Note]] = {
        instrument_id: [] for instrument_id in instrument_info
    }
    lyrics: List[Lyric] = []
    ties: Dict[Tuple[str, int], int] = {}

    # Initialize variables
    time = 0
    velocity = 64
    division = 1
    default_instrument_id = next(iter(instrument_info))
    transpose_semitone = 0
    transpose_octave = 0

    # Iterate over all elements
    for measure_elem in part_elem.findall("measure"):

        # Initialize position
        position = 0
        last_note_position = None

        for elem in measure_elem:

            # TODO: Handle repeat, segno, dalsegno, coda, tocoda, fine

            if elem.tag == "attributes":
                # Division
                division_elem = elem.find("divisions")
                if (
                    division_elem is not None
                    and division_elem.text is not None
                ):
                    division = int(division_elem.text)

                # Transpose
                transpose_elem = elem.find("transpose")
                if transpose_elem is not None:
                    transpose_semitone = int(
                        _get_required_text(transpose_elem, "chromatic")
                    )
                    octave_change = _get_text(transpose_elem, "octave-change")
                    if octave_change is not None:
                        transpose_octave = int(octave_change)

                # Time signatures
                time_elem = elem.find("time")
                if time_elem is not None:
                    # Numerator
                    beats = _get_required_text(time_elem, "beats")
                    if "+" in beats:
                        numerator = sum(int(beat) for beat in beats.split("+"))
                    else:
                        numerator = int(beats)

                    # Denominator
                    beat_type = _get_required_text(time_elem, "beat-type")
                    if "+" in beat_type:
                        raise RuntimeError(
                            "Compound time signatures with separate fractions "
                            "are not supported."
                        )
                    denominator = int(beat_type)
                    time_signatures.append(
                        TimeSignature(
                            time=time + position,
                            numerator=numerator,
                            denominator=denominator,
                        )
                    )

                # Key signatures
                key_elem = elem.find("key")
                if key_elem is not None:
                    parsed_key = parse_key_elem(key_elem)
                    if parsed_key is not None:
                        key_signatures.append(
                            KeySignature(
                                time=time + position,
                                root=parsed_key.get("root"),
                                mode=parsed_key.get("mode"),
                                root_str=parsed_key.get("root_str"),
                            )
                        )

            # Sound element
            elif elem.tag == "sound":

                # Tempo
                tempo = elem.get("tempo")
                if tempo is not None:
                    tempos.append(Tempo(time + position, float(tempo)))

                # Dynamics
                dynamics = elem.get("dynamics")
                if dynamics is not None:
                    velocity = int(float(dynamics))

            elif elem.tag == "direction":
                # TODO: Handle symbolic dynamics and tempo

                tempo_set = False

                # Sound element
                sound_elem = elem.find("sound")
                if sound_elem is not None:
                    # Tempo
                    tempo = sound_elem.get("tempo")
                    if tempo is not None:
                        tempos.append(
                            Tempo(time=time + position, qpm=float(tempo))
                        )
                        tempo_set = True

                    # Dynamics
                    dynamics = sound_elem.get("dynamics")
                    if dynamics is not None:
                        velocity = int(float(dynamics))

                # Metronome element
                if not tempo_set:
                    metronome_elem = elem.find("direction-type/metronome")
                    if metronome_elem is not None:
                        qpm = parse_metronome_elem(metronome_elem)
                        if qpm is not None:
                            tempos.append(Tempo(time=time + position, qpm=qpm))

            elif elem.tag == "note":
                # TODO: Handle voice information

                # Check if it is a rest
                rest_elem = elem.find("rest")
                if rest_elem is not None:
                    duration = int(_get_required_text(elem, "duration"))
                    position += int(duration * resolution / division)
                    continue

                # Check if it is a cue note
                if elem.find("cue") is not None:
                    continue

                # Check if it is an unpitched note
                # TODO: Handle unpitched notes
                unpitched_elem = elem.find("unpitched")
                if unpitched_elem is not None:
                    continue

                # Move time position backward if it is in a chord
                if elem.find("chord") is not None:
                    if last_note_position is not None:
                        position = last_note_position

                # Compute pitch number
                pitch, pitch_str = parse_pitch_elem(
                    _get_required(elem, "pitch")
                )
                pitch += 12 * transpose_octave + transpose_semitone

                # Get instrument information
                instrument_elem = elem.find("instrument")
                if instrument_elem is not None:
                    instrument_id = _get_required_text(instrument_elem, "id")
                    if instrument_id not in instrument_info:
                        raise MusicXMLError(
                            "ID of an 'instrument' element must be predefined "
                            "in a 'score-instrument' element."
                        )
                else:
                    instrument_id = default_instrument_id

                # Check if it is a grace note
                grace_elem = elem.find("grace")
                if grace_elem is not None:
                    note_type = _get_required_text(elem, "type")
                    notes[instrument_id].append(
                        Note(
                            time=time + position,
                            pitch=pitch,
                            duration=int(
                                NOTE_TYPE_MAP[note_type] * resolution
                            ),
                            velocity=velocity,
                            pitch_str=pitch_str,
                        )
                    )
                    continue

                # Get duration
                # TODO: Should we look for a 'duration' or 'type' element?
                duration = int(_get_required_text(elem, "duration"))

                # Check if it is a tied note
                # TODO: Should we look for a 'tie' or 'tied' element?
                is_outgoing_tie = False
                for tie_elem in elem.findall("tie"):
                    if tie_elem.get("type") == "start":
                        is_outgoing_tie = True

                # Check if it is an incoming tied note
                note_key = (instrument_id, pitch)
                if note_key in ties:
                    note_idx = ties[note_key]
                    notes[instrument_id][note_idx].duration += int(
                        duration * resolution / division
                    )

                    if is_outgoing_tie:
                        ties[note_key] = note_idx
                    else:
                        del ties[note_key]

                else:
                    # Create a new note and append it to the note list
                    notes[instrument_id].append(
                        Note(
                            time=time + position,
                            pitch=pitch,
                            duration=int(duration * resolution / division),
                            velocity=velocity,
                            pitch_str=pitch_str,
                        )
                    )

                    if is_outgoing_tie:
                        ties[note_key] = len(notes[instrument_id]) - 1

                # Lyric
                lyric_elem = elem.find("lyric")
                if lyric_elem is not None:
                    lyric_text = _get_required_text(lyric_elem, "text")
                    syllabic_elem = lyric_elem.find("syllabic")
                    if syllabic_elem is not None:
                        if syllabic_elem.text == "begin":
                            lyric_text += "-"
                        elif syllabic_elem.text == "middle":
                            lyric_text = "-" + lyric_text + "-"
                        elif syllabic_elem.text == "end":
                            lyric_text = "-" + lyric_text
                    lyrics.append(
                        Lyric(time=time + position, lyric=lyric_text)
                    )

                # Move time position forward if it is not in chord
                last_note_position = position
                position += int(duration * resolution / division)

            elif elem.tag == "forward":
                duration = int(_get_required_text(elem, "duration"))
                position += int(duration * resolution / division)

            elif elem.tag == "backup":
                duration = int(_get_required_text(elem, "duration"))
                position -= int(duration * resolution / division)

        time += position

    # Sort notes
    for instrument_notes in notes.values():
        instrument_notes.sort(
            key=attrgetter("time", "pitch", "duration", "velocity")
        )

    # Sort tempos, key signatures, time signatures and lyrics
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))
    lyrics.sort(key=attrgetter("time"))

    return {
        "tempos": tempos,
        "key_signatures": key_signatures,
        "time_signatures": time_signatures,
        "notes": notes,
        "lyrics": lyrics,
    }


def parse_metadata(root: Element) -> Metadata:
    """Return a Metadata object parsed from a MusicXML file."""
    # Title is usually stored in movement-title. See
    # https://www.musicxml.com/tutorial/file-structure/score-header-entity/
    title = _get_text(root, "movement-title", remove_newlines=True)
    if not title:
        title = _get_text(root, "work/work-title", remove_newlines=True)

    # Creators and copyrights
    creators = []
    copyrights = []

    identification_elem = root.find("identification")
    if identification_elem is not None:
        for creator_elem in identification_elem.findall("creator"):
            if creator_elem.text:
                creators.append(creator_elem.text)
        for right_elem in identification_elem.findall("rights"):
            if right_elem.text:
                copyrights.append(right_elem.text)

    return Metadata(
        title=title,
        creators=creators,
        copyright=" ".join(copyrights) if copyrights else None,
        source_format="musicxml",
    )


def _get_root(path: Union[str, Path], compressed: bool = None):
    """Return root of the element tree."""
    if compressed is None:
        compressed = str(path).endswith(".mxl")

    if not compressed:
        tree = ET.parse(str(path))
        return tree.getroot()

    # Find out the main MusicXML file in the compressed ZIP archive
    # according to the official tutorial (see
    # https://www.musicxml.com/tutorial/compressed-mxl-files/).
    zip_file = ZipFile(str(path))
    if "META-INF/container.xml" not in zip_file.namelist():
        raise MusicXMLError("Container file ('container.xml') not found.")
    container = ET.fromstring(zip_file.read("META-INF/container.xml"))
    rootfile = container.find("rootfiles/rootfile")
    if rootfile is None:
        raise MusicXMLError(
            "Element 'rootfile' tag not found in the container file "
            "('container.xml')."
        )
    filename = _get_required_attr(rootfile, "full-path")
    return ET.fromstring(zip_file.read(filename))


def _get_divisions(root: Element):
    """Return a list of divisions."""
    divisions = []
    for division_elem in root.findall("part/measure/attributes/divisions"):
        if division_elem.text is None:
            continue
        if not float(division_elem.text).is_integer():
            raise MusicXMLError(
                "Noninteger 'division' values are not supported."
            )
        divisions.append(int(division_elem.text))
    return divisions


def parse_score_part_elem(elem: Element) -> Tuple[str, OrderedDict]:
    """Return part information parsed from a score part element."""
    # Part ID
    part_id = _get_required_attr(elem, "id")

    # Part name
    part_name = _get_text(elem, "part-name", remove_newlines=True)

    # Instruments
    part_info: OrderedDict = OrderedDict()
    for score_instrument_elem in elem.findall("score-instrument"):
        instrument_id = _get_required_attr(score_instrument_elem, "id")
        part_info[instrument_id] = OrderedDict()
        part_info[instrument_id]["name"] = _get_text(
            score_instrument_elem,
            "instrument-name",
            part_name,
            remove_newlines=True,
        )
    for midi_instrument_elem in elem.findall("midi-instrument"):
        instrument_id = _get_required_attr(midi_instrument_elem, "id")
        if instrument_id not in part_info:
            if instrument_id == part_id:
                instrument_id = ""
                part_info[""] = {"name": part_name}
            else:
                raise MusicXMLError(
                    "ID of a 'midi-instrument' element must be predefined "
                    "in a 'score-instrument' element."
                )
        part_info[instrument_id]["program"] = int(
            _get_text(midi_instrument_elem, "midi-program", 0)
        )
        part_info[instrument_id]["is_drum"] = (
            int(_get_text(midi_instrument_elem, "midi-channel", 0)) == 10
        )
    if not part_info:
        part_info[""] = {"name": part_name}
    for value in part_info.values():
        if "program" not in value:
            value["program"] = 0
        if "is_drum" not in value:
            value["is_drum"] = False
    return part_id, part_info


def read_musicxml(
    path: Union[str, Path], resolution: int = None, compressed: bool = None,
) -> Music:
    """Read a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MusicXML file to read.
    resolution : int, optional
        Time steps per quarter note. Defaults to the least common
        multiple of all divisions.
    compressed : bool, optional
        Whether it is a compressed MusicXML file. Defaults to infer
        from the filename.

    Returns
    -------
    :class:`muspy.Music`
        Converted Music object.

    Notes
    -----
    Grace notes and unpitched notes are not supported.

    """
    # Get element tree root
    root = _get_root(path, compressed)

    if root.tag == "score-timewise":
        raise ValueError("MusicXML file with timewise type is not supported.")

    # Meta data
    metadata = parse_metadata(root)
    metadata.source_filename = Path(path).name

    # Set resolution to the least common multiple of all divisions
    if resolution is None:
        divisions = _get_divisions(root)
        resolution = _lcm(*divisions) if divisions else 1

    # Part information
    part_info: OrderedDict = OrderedDict()
    for part_elem in root.findall("part-list/score-part"):
        part_id, info = parse_score_part_elem(part_elem)
        part_info[part_id] = info

    if root.find("part") is None:
        return Music(metadata=metadata, resolution=resolution)

    # Initialize lists
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    tracks: List[Track] = []

    # Raise an error if part-list information is missing for a
    # multi-part piece
    if not part_info:
        if len(root.findall("part")) > 1:
            raise MusicXMLError(
                "Part-list information is required for a multi-part piece."
            )
        part_elem = _get_required(root, "part")
        instrument_info = {"": {"program": 0, "is_drum": False}}
        part = parse_part_elem(part_elem, resolution, instrument_info)

    else:
        # Iterate over all parts and measures
        for part_elem in root.findall("part"):
            part_id = part_elem.get("id")  # type: ignore
            if part_id is None:
                if len(root.findall("part")) > 1:
                    continue
                part_id = next(iter(part_info))
            if part_id not in part_info:
                continue

            # Parse part
            part = parse_part_elem(part_elem, resolution, part_info[part_id])

            # Extend lists
            tempos.extend(part["tempos"])
            key_signatures.extend(part["key_signatures"])
            time_signatures.extend(part["time_signatures"])
            for instrument_id, notes in part["notes"].items():
                track = Track(
                    program=part_info[part_id][instrument_id]["program"],
                    is_drum=part_info[part_id][instrument_id]["is_drum"],
                    name=part_info[part_id][instrument_id]["name"],
                    notes=notes,
                    lyrics=part["lyrics"],
                )
                tracks.append(track)

    # Sort tempos, key signatures and time signatures
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))

    return Music(
        metadata=metadata,
        resolution=resolution,
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        tracks=tracks,
    )
