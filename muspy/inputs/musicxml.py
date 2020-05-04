"""MusicXML input interface."""
import warnings
import xml.etree.ElementTree as ET
from collections import OrderedDict
from functools import reduce
from pathlib import Path
from typing import Any, List, Optional, Union, Dict
from xml.etree.ElementTree import Element
from zipfile import ZipFile

import xmlschema

from ..classes import (
    KeySignature,
    Lyric,
    MetaData,
    Note,
    SongInfo,
    SourceInfo,
    Tempo,
    TimeSignature,
    Timing,
    Track,
)
from ..music import Music
from ..schemas import get_musicxml_schema_path

KEY_MAP = (
    "Cb",
    "Gb",
    "Db",
    "Ab",
    "Eb",
    "Bb",
    "F",
    "C",
    "G",
    "D",
    "A",
    "E",
    "B",
    "F#",
    "C#",
)

STEP_MAP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


class MusicXMLElementError(Exception):
    """An error class for missing element in MusicXML file."""


class CompressedMusicXMLFileError(Exception):
    """An error class for an invalid compressed MusicXML file."""


def _gcd(a: int, b: int) -> int:
    """Return greatest common divisor using Euclid's Algorithm.

    Code copied from https://stackoverflow.com/a/21912744.

    """
    while b:
        a, b = b, a % b
    return a


def _lcm(a: int, b: int) -> int:
    """Return lowest common multiple.

    Code copied from https://stackoverflow.com/a/21912744.

    """
    return a * b // _gcd(a, b)


def lcm(*args: List[int]) -> int:
    """Return lcm of args.

    Code copied from https://stackoverflow.com/a/21912744.

    """
    return reduce(_lcm, args)[0]  # type: ignore


def validate_musicxml(path: Union[str, Path]):
    """Validate a file against the MusicXML schema; raise errors if invalid."""
    schema = xmlschema.XMLSchema(get_musicxml_schema_path())
    schema.validate(str(path))


def get_text(element: Element, path: str, default: Any = None):
    """Return the text of the first matching element."""
    elem = element.find(path)
    if elem is not None and elem.text is not None:
        return elem.text
    return default


def get_required(element: Element, path: str) -> Element:
    """Return a required element; raise ValueError if not found."""
    elem = element.find(path)
    if elem is None:
        raise MusicXMLElementError("Element `{}` is required.".format(path))
    return elem


def get_required_text(element: Element, path: str) -> str:
    """Return the text of a required element; raise ValueError if not found."""
    elem = element.find(path)
    if elem is None:
        raise MusicXMLElementError(
            "Subelement '{}' is required for element '{}'."
            "".format(path, element.tag)
        )
    if elem.text is None:
        raise MusicXMLElementError(
            "Subelement '{}' of element '{}' should not be empty."
            "".format(path, element.tag)
        )
    return elem.text


def parse_part(
    part_elem: Element, resolution: int, instrument_info: dict
) -> dict:
    """Return a dictionary containing data parsed from a part."""
    # Initialize lists
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    lyrics: List[Lyric] = []
    tempos: List[Tempo] = []
    notes: Dict[str, List[Note]] = {
        instrument_id: [] for instrument_id in instrument_info
    }

    # Initialize time
    time = 0
    velocity = 64
    factor = resolution
    default_instrument_id = next(iter(instrument_info))

    # Iterate over all elements
    for measure_elem in part_elem.findall("measure"):

        # Initialize position
        position = 0

        for elem in measure_elem:

            # TODO: handle repeat, segno, dalsegno, coda, tocoda, fine
            if elem.tag == "attributes":
                # Division
                division_elem = elem.find("divisions")
                if (
                    division_elem is not None
                    and division_elem.text is not None
                ):
                    if position > 0:
                        warnings.warn(
                            "Resolution changes in the middle of a measure.",
                            RuntimeWarning,
                        )
                    factor = resolution // int(division_elem.text)

                # Time signatures
                time_elem = elem.find("time")
                if time_elem is not None:
                    numerator = int(get_required_text(time_elem, "beats"))
                    denominator = int(
                        get_required_text(time_elem, "beat-type")
                    )
                    time_signatures.append(
                        TimeSignature(
                            time=time + position,
                            numerator=numerator,
                            denominator=denominator,
                        )
                    )

                # Key signatures
                # TODO: handle transposed keys
                key_elem = elem.find("key")
                if key_elem is not None:
                    fifths = int(get_required_text(key_elem, "fifths"))
                    mode = get_text(key_elem, "mode", "major")
                    key_signatures.append(
                        KeySignature(
                            time=time + position,
                            root=KEY_MAP[fifths + 7],
                            mode=mode,
                        )
                    )

            elif elem.tag == "directions":
                sound_elem = elem.find("sound")
                if sound_elem is None:
                    continue
                if "tempo" in sound_elem.attrib:
                    tempos.append(
                        Tempo(time + position, int(sound_elem.attrib["tempo"]))
                    )
                # TODO: dynamic -> velocity

            # TODO: lyrics

            elif elem.tag == "note":
                # Check if it is a rest
                grace_elem = elem.find("grace")
                if grace_elem is not None:
                    continue

                # Check if it is an unpitched note
                unpitched_elem = elem.find("unpitched")
                if unpitched_elem is not None:
                    warnings.warn(
                        "Got unpitched notes; ignore it anyway.",
                        RuntimeWarning,
                    )
                    continue

                # Get duration
                # print("=== {} ===".format(elem))
                # for child in elem:
                #     print(child)
                duration = int(get_required_text(elem, "duration"))

                # Check if it is a rest
                rest_elem = elem.find("rest")
                if rest_elem is not None:
                    position += duration * factor
                    continue

                # Get pitch
                pitch_elem = elem.find("pitch")
                if pitch_elem is None:
                    raise MusicXMLElementError(
                        "Element 'pitch' is required for element 'note'."
                    )
                step = get_required_text(pitch_elem, "step")
                octave = int(get_required_text(pitch_elem, "octave"))
                alter = int(get_required_text(pitch_elem, "octave"))
                pitch = STEP_MAP[step] + alter + octave * 8

                # Create a note and append it to the note list
                note = Note(
                    time + position,
                    time + position + duration * factor,
                    pitch,
                    velocity,
                )
                instrument_elem = elem.find("instrument")
                if instrument_elem is not None:
                    instrument_id = instrument_elem.get("id")
                    if instrument_id is None:
                        raise MusicXMLElementError(
                            "Instrument ID must not be None."
                        )
                    if instrument_id not in instrument_info:
                        raise MusicXMLElementError(
                            "Instrument ID must be specified in a "
                            "'score-instrument' element."
                        )
                    notes[instrument_id].append(note)
                else:
                    notes[default_instrument_id].append(note)

                # Move time position forward if it is not in chord
                chord = elem.find("chord")
                if chord is None:
                    position += duration * factor

            elif elem.tag == "forward":
                duration = int(get_required_text(elem, "duration"))
                position += duration * factor

            elif elem.tag == "backup":
                duration = int(get_required_text(elem, "duration"))
                position -= duration * factor

        time += position

    return {
        "key_signatures": key_signatures,
        "time_signatures": time_signatures,
        "lyrics": lyrics,
        "tempos": tempos,
        "notes": notes,
    }


def read_musicxml(
    path: Union[str, Path], compressed: Optional[bool] = None
) -> Music:
    """Read a MusicXML file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MusicXML file to be read.

    Notes
    -----
    Unpitched instruments are not supported. Grace notes and unpitched notes
    are ignored.

    """
    if compressed is None:
        compressed = str(path).endswith(".mxl")

    if compressed:
        # Find out the main MusicXML file in the compressed ZIP archive
        # according to the official tutorial (see
        # https://www.musicxml.com/tutorial/compressed-mxl-files/).
        zip_file = ZipFile(str(path))
        if "META-INF/container.xml" not in zip_file.namelist():
            raise CompressedMusicXMLFileError(
                "Container file ('container.xml') not found."
            )
        container = ET.fromstring(zip_file.read("META-INF/container.xml"))
        rootfile = container.find("rootfiles/rootfile")
        if rootfile is None:
            raise CompressedMusicXMLFileError(
                "Element 'rootfile' tag not found in the container file "
                "('container.xml')."
            )
        filename = rootfile.get("full-path")
        if filename is None:
            raise CompressedMusicXMLFileError(
                "Subelement 'full-path' of 'rootfile' is not defined."
            )
        root = ET.fromstring(zip_file.read(filename))
    else:
        tree = ET.parse(str(path))
        root = tree.getroot()

    if root.tag == "score-timewise":
        raise ValueError("MusicXML file with timewise type is not supported.")

    # Meta data
    title = get_text(root, "work/work-title")
    creators = []
    copyright_ = ""

    identification_elem = root.find("identification")
    if identification_elem is not None:
        for creator_elem in identification_elem.findall("creator"):
            if creator_elem.text is not None:
                creators.append(creator_elem.text)
        for right_elem in identification_elem.findall("rights"):
            if right_elem.text is not None:
                copyright_ += right_elem.text

    # Set resolution to the least common multiple of all divisions
    divisions = []
    for division_elem in root.findall("part/measure/attributes/divisions"):
        if division_elem.text is None:
            continue
        if not float(division_elem.text).is_integer():
            raise MusicXMLElementError(
                "Noninteger 'division' values are not supported."
            )
        divisions.append(int(division_elem.text))
    resolution = lcm(divisions)

    # Part information
    part_names: OrderedDict = OrderedDict()
    part_info: OrderedDict = OrderedDict()
    for part_elem in root.findall("part-list/score-part"):
        part_id = part_elem.get("id")

        # Part name
        part_names[part_id] = get_text(part_elem, "part-name")

        # Instruments
        part_info[part_id] = OrderedDict()
        for score_instrument_elem in part_elem.findall("score-instrument"):
            instrument_id = score_instrument_elem.get("id")
            part_info[part_id][instrument_id] = OrderedDict()
            part_info[part_id][instrument_id]["name"] = get_text(
                score_instrument_elem, "instrument-name"
            )
        for midi_instrument_elem in part_elem.findall("midi-instrument"):
            instrument_id = midi_instrument_elem.get("id")
            if instrument_id not in part_info[part_id]:
                if instrument_id == part_id:
                    instrument_id = ""
                    part_info[part_id][""] = {"name": None}
                else:
                    raise MusicXMLElementError(
                        "ID of a 'midi-instrument' element must be "
                        "specified in a 'score-instrument' element."
                    )
            part_info[part_id][instrument_id]["program"] = get_text(
                midi_instrument_elem, "midi-program", 0
            )
            part_info[part_id][instrument_id]["is_drum"] = (
                get_text(midi_instrument_elem, "midi-channel", 0) == 10
            )
        if not part_info[part_id]:
            part_info[part_id][""] = {"name": None}
        for value in part_info[part_id].values():
            if "program" not in value:
                value["program"] = 0
            if "is_drum" not in value:
                value["is_drum"] = False

    # Initialize lists
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    lyrics: List[Lyric] = []
    tempos: List[Tempo] = []
    tracks: List[Track] = []

    default_part_id = next(iter(part_info))

    # Iterate over all parts and measures
    for part_elem in root.findall("part"):
        part_id = part_elem.get("id", default_part_id)
        part = parse_part(part_elem, resolution, part_info[part_id])
        key_signatures.extend(part["key_signatures"])
        time_signatures.extend(part["time_signatures"])
        for instrument_id, notes in part["notes"].items():
            track = Track(
                program=part_info[part_id][instrument_id]["program"],
                is_drum=part_info[part_id][instrument_id]["is_drum"],
                name=part_info[part_id][instrument_id]["name"],
                notes=notes,
            )
            tracks.append(track)

    meta = MetaData(
        song=SongInfo(title=title, creators=creators),
        source=SourceInfo(
            filename=Path(path).name, format="musicxml", copyright=copyright_
        ),
    )
    timing = Timing(is_metrical=True, resolution=resolution, tempos=tempos)

    return Music(
        meta=meta,
        timing=timing,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        lyrics=lyrics,
        tracks=tracks,
    )
