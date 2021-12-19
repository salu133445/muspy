"""MuseScore input interface."""
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


class MuseScoreError(Exception):
    """A class for MuseScore related errors."""


class MuseScoreWarning(Warning):
    """A class for MuseScore related warnings."""


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
        raise MuseScoreError("Element `{}` is required.".format(path))
    return elem


def _get_required_attr(element: Element, attr: str) -> str:
    """Return a required attribute; raise MuseScoreError if not found."""
    attribute = element.get(attr)
    if attribute is None:
        raise MuseScoreError("Attribute '{}' is required for an element ")
    return attribute


def _get_required_text(
    element: Element, path: str, remove_newlines: bool = False
) -> str:
    """Return a required text; raise MuseScoreError if not found."""
    elem = element.find(path)
    if elem is None:
        raise MuseScoreError(
            "Child element '{}' is required for an element '{}'."
            "".format(path, element.tag)
        )
    if elem.text is None:
        raise MuseScoreError(
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


def parse_time_elem(elem: Element) -> Tuple[int, int]:
    """Return the numerator and denominator parsed from a time element."""
    # Numerator
    beats = _get_required_text(elem, "sigN")
    if "+" in beats:
        numerator = sum(int(beat) for beat in beats.split("+"))
    else:
        numerator = int(beats)

    # Denominator
    beat_type = _get_required_text(elem, "sigD")
    if "+" in beat_type:
        raise RuntimeError(
            "Compound time signatures with separate fractions "
            "are not supported."
        )
    denominator = int(beat_type)

    return numerator, denominator


def parse_key_elem(elem: Element) -> Dict:
    """Return a dictionary with data parsed from a key element."""
    mode = _get_text(elem, "mode", "major")
    accidental = int(_get_required_text(elem, "accidental"))
    if mode is None:
        return {"accidental": accidental}
    idx = MODE_CENTERS[mode] + accidental
    if idx < 0 or idx > 20:
        return {"accidental": accidental, "mode": mode}
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + accidental]
    return {
        "root": root,
        "mode": mode,
        "accidental": accidental,
        "root_str": root_str,
    }


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


def parse_staff_elem(
    staff_elem: Element, resolution: int, instrument_info: dict
) -> dict:
    """Return a dictionary with data parsed from a staff element."""
    # Initialize lists and placeholders
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    notes: List[Note] = []
    lyrics: List[Lyric] = []
    ties: Dict[int, int] = {}

    # Initialize variables
    time = 0
    velocity = 64
    # division = 1
    # transpose_semitone = 0
    # transpose_octave = 0
    # Repeats
    is_repeat = 0
    # last_repeat = 0
    start_repeat = 0
    count_repeat = 1
    count_ending = 1
    # # Coda, tocoda, dacapo, segno, dalsegno, fine
    # is_after_jump = False
    # is_fine = False
    # is_dacapo = False
    # is_dalsegno = False
    # is_segno = False
    # is_segno_found = False
    # is_tocoda = False
    # is_coda = False
    # is_coda_found = False
    # Tuple
    is_tuple = False

    # Iterate over all elements
    measure_idx = 0
    measure_elems = list(staff_elem.findall("Measure"))
    while measure_idx < len(measure_elems):

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Set the default next measure
        next_measure_idx = measure_idx + 1

        # Initialize position
        position = 0
        last_note_position = None

        # # Look for segno
        # if is_dalsegno and not is_segno_found:
        #     # Segno
        #     for sound_elem in measure_elem.findall("sound"):
        #         if sound_elem.get("segno") is not None:
        #             is_segno = True
        #     for sound_elem in measure_elem.findall("direction/sound"):
        #         if sound_elem.get("segno") is not None:
        #             is_segno = True

        #     # Skip if not segno
        #     if not is_segno:
        #         measure_idx += 1
        #         continue

        #     is_segno_found = True

        # # Look for coda
        # if is_tocoda and not is_coda_found:
        #     # Coda
        #     for sound_elem in measure_elem.findall("sound"):
        #         if sound_elem.get("coda") is not None:
        #             is_coda = True
        #     for sound_elem in measure_elem.findall("direction/sound"):
        #         if sound_elem.get("coda") is not None:
        #             is_coda = True

        #     # Skip if not coda
        #     if not is_coda:
        #         measure_idx += 1
        #         continue

        #     is_coda_found = True

        # # Sound element
        # for sound_elem in measure_elem.findall("sound"):
        #     if is_after_jump:
        #         # Tocoda
        #         if sound_elem.get("tocoda") is not None:
        #             is_tocoda = True

        #         # Fine
        #         if sound_elem.get("fine") is not None:
        #             is_fine = True
        #     else:
        #         # Dacapo
        #         if sound_elem.get("dacapo") is not None:
        #             is_dacapo = True

        #         # Daselgno
        #         if sound_elem.get("dalsegno") is not None:
        #             is_dalsegno = True

        # # Sound elements under direction elements
        # for sound_elem in measure_elem.findall("direction/sound"):
        #     if is_after_jump:
        #         # Tocoda
        #         if sound_elem.get("tocoda") is not None:
        #             is_tocoda = True

        #         # Fine
        #         if sound_elem.get("fine") is not None:
        #             is_fine = True
        #     else:
        #         # Dacapo
        #         if sound_elem.get("dacapo") is not None:
        #             is_dacapo = True

        #         # Daselgno
        #         if sound_elem.get("dalsegno") is not None:
        #             is_dalsegno = True

        if measure_elem.find("startRepeat"):
            start_repeat = measure_idx

        # Voice elements
        for voice_elem in measure_elem.findall("voice"):
            for elem in voice_elem:
                # Ket signatures
                if elem.tag == "KeySig":
                    parsed_key = parse_key_elem(elem)
                    if parsed_key is not None:
                        key_signatures.append(
                            KeySignature(
                                time=time + position,
                                root=parsed_key.get("root"),
                                mode=parsed_key.get("mode"),
                                root_str=parsed_key.get("root_str"),
                            )
                        )

                # Time signatures
                if elem.tag == "TimeSig":
                    numerator, denominator = parse_time_elem(elem)
                    time_signatures.append(
                        TimeSignature(
                            time=time + position,
                            numerator=numerator,
                            denominator=denominator,
                        )
                    )

                # Dynamic elements
                if elem.tag == "Dynamic":
                    velocity = round(
                        float(_get_required_text(elem, "velocity"))
                    )

                # Tempo elements
                if elem.tag == "Tempo":
                    tempos.append(
                        Tempo(
                            time + position,
                            60 * float(_get_required_text(elem, "tempo")),
                        )
                    )

                # Tuplet elements
                if elem.tag == "Tuplet":
                    is_tuple = True
                    normal_notes = int(_get_required_text(elem, "normalNotes"))
                    actual_notes = int(_get_required_text(elem, "actualNotes"))
                    tuple_ratio = normal_notes / actual_notes

                # Chord elements
                if elem.tag == "Chord":
                    # Compute duration
                    duration_type = _get_required_text(elem, "durationType")
                    duration = NOTE_TYPE_MAP[duration_type] * resolution

                    # Handle tuplets
                    if is_tuple:
                        duration *= tuple_ratio

                    # Handle dots
                    dots_elem = elem.find("dots")
                    if dots_elem is not None and dots_elem.text:
                        duration *= 2 - 0.5 ** int(dots_elem.text)

                    # Round the duration
                    duration = round(duration)

                    # Collect notes
                    for note_elem in elem.findall("Note"):
                        pitch = int(_get_required_text(note_elem, "pitch"))
                        notes.append(
                            Note(
                                time=time + position,
                                pitch=pitch,
                                duration=duration,
                                velocity=velocity,
                            )
                        )
                    position += duration

                # Handle last tuplet note
                if elem.tag == "endTuplet":
                    old_duration = round(
                        NOTE_TYPE_MAP[duration_type] * resolution
                    )
                    new_duration = normal_notes * old_duration - (
                        actual_notes - 1
                    ) * round(old_duration * tuple_ratio)
                    if notes[-1].duration != new_duration:
                        notes[-1].duration = new_duration
                        position += new_duration - duration
                    is_tuple = False

                # Spanner elements
                if elem.tag == "Spanner":
                    if elem.get("type") == "Volta":
                        # elem.find("Volta/endings")
                        next_measure_location = _get_text(
                            elem, "next/location/measures"
                        )
                        if next_measure_location is not None:
                            next_measure_idx = int(next_measure_location)

        if measure_elem.find("endRepeat"):
            next_measure_idx = start_repeat

        # # Iterating over all elements in the current measure
        # for elem in measure_elem:
        #     # Attributes elements
        #     if elem.tag == "attributes":
        #         # Division elements
        #         division_elem = elem.find("divisions")
        #         if (
        #             division_elem is not None
        #             and division_elem.text is not None
        #         ):
        #             division = int(division_elem.text)

        #         # Transpose elements
        #         transpose_elem = elem.find("transpose")
        #         if transpose_elem is not None:
        #             transpose_semitone = int(
        #                 _get_required_text(transpose_elem, "chromatic")
        #             )
        #             octave_change = _get_text(transpose_elem, "octave-change")
        #             if octave_change is not None:
        #                 transpose_octave = int(octave_change)

        #         # Time signatures
        #         time_elem = elem.find("time")
        #         if time_elem is not None:
        #             # Numerator
        #             beats = _get_required_text(time_elem, "beats")
        #             if "+" in beats:
        #                 numerator = sum(int(beat) for beat in beats.split("+"))
        #             else:
        #                 numerator = int(beats)

        #             # Denominator
        #             beat_type = _get_required_text(time_elem, "beat-type")
        #             if "+" in beat_type:
        #                 raise RuntimeError(
        #                     "Compound time signatures with separate fractions "
        #                     "are not supported."
        #                 )
        #             denominator = int(beat_type)
        #             time_signatures.append(
        #                 TimeSignature(
        #                     time=time + position,
        #                     numerator=numerator,
        #                     denominator=denominator,
        #                 )
        #             )

        #         # Key elements
        #         key_elem = elem.find("key")
        #         if key_elem is not None:
        #             parsed_key = parse_key_elem(key_elem)
        #             if parsed_key is not None:
        #                 key_signatures.append(
        #                     KeySignature(
        #                         time=time + position,
        #                         root=parsed_key.get("root"),
        #                         mode=parsed_key.get("mode"),
        #                         root_str=parsed_key.get("root_str"),
        #                     )
        #                 )

        #     # Sound element
        #     elif elem.tag == "sound":
        #         # Tempo elements
        #         tempo = elem.get("tempo")
        #         if tempo is not None:
        #             tempos.append(Tempo(time + position, float(tempo)))

        #         # Dynamics elements
        #         dynamics = elem.get("dynamics")
        #         if dynamics is not None:
        #             velocity = round(float(dynamics))

        #     # Direction elements
        #     elif elem.tag == "direction":
        #         # TODO: Handle symbolic dynamics and tempo

        #         tempo_set = False

        #         # Sound elements
        #         sound_elem_ = elem.find("sound")
        #         if sound_elem_ is not None:
        #             # Tempo directions
        #             tempo = sound_elem_.get("tempo")
        #             if tempo is not None:
        #                 tempos.append(
        #                     Tempo(time=time + position, qpm=float(tempo))
        #                 )
        #                 tempo_set = True

        #             # Dynamic directions
        #             dynamics = sound_elem_.get("dynamics")
        #             if dynamics is not None:
        #                 velocity = round(float(dynamics))

        #         # Metronome elements
        #         if not tempo_set:
        #             metronome_elem = elem.find("direction-type/metronome")
        #             if metronome_elem is not None:
        #                 qpm = parse_metronome_elem(metronome_elem)
        #                 if qpm is not None:
        #                     tempos.append(Tempo(time=time + position, qpm=qpm))

        #     # Note elements
        #     elif elem.tag == "note":
        #         # TODO: Handle voice information

        #         # Rest elements
        #         rest_elem = elem.find("rest")
        #         if rest_elem is not None:
        #             # Move time position forward if it is a rest
        #             duration = int(_get_required_text(elem, "duration"))
        #             position += round(duration * resolution / division)
        #             continue

        #         # Cue notes
        #         if elem.find("cue") is not None:
        #             continue

        #         # Unpitched notes
        #         # TODO: Handle unpitched notes
        #         unpitched_elem = elem.find("unpitched")
        #         if unpitched_elem is not None:
        #             continue

        #         # Chord elements
        #         if elem.find("chord") is not None:
        #             # Move time position backward if it is in a chord
        #             if last_note_position is not None:
        #                 position = last_note_position

        #         # Compute pitch number
        #         pitch, pitch_str = parse_pitch_elem(
        #             _get_required(elem, "pitch")
        #         )
        #         pitch += 12 * transpose_octave + transpose_semitone

        #         # Grace notes
        #         grace_elem = elem.find("grace")
        #         if grace_elem is not None:
        #             note_type = _get_required_text(elem, "type")
        #             notes.append(
        #                 Note(
        #                     time=time + position,
        #                     pitch=pitch,
        #                     duration=round(
        #                         NOTE_TYPE_MAP[note_type] * resolution
        #                     ),
        #                     velocity=velocity,
        #                     pitch_str=pitch_str,
        #                 )
        #             )
        #             continue

        #         # Get duration
        #         # TODO: Should we look for a duration or type element?
        #         duration = int(_get_required_text(elem, "duration"))

        #         # Check if it is a tied note
        #         # TODO: Should we look for a tie or tied element?
        #         is_outgoing_tie = False
        #         for tie_elem in elem.findall("tie"):
        #             if tie_elem.get("type") == "start":
        #                 is_outgoing_tie = True

        #         # Check if it is an incoming tied note
        #         if pitch in ties:
        #             note_idx = ties[pitch]
        #             notes[note_idx].duration += round(
        #                 duration * resolution / division
        #             )

        #             if is_outgoing_tie:
        #                 ties[pitch] = note_idx
        #             else:
        #                 del ties[pitch]

        #         else:
        #             # Create a new note and append it to the note list
        #             notes.append(
        #                 Note(
        #                     time=time + position,
        #                     pitch=pitch,
        #                     duration=round(duration * resolution / division),
        #                     velocity=velocity,
        #                     pitch_str=pitch_str,
        #                 )
        #             )

        #             if is_outgoing_tie:
        #                 ties[pitch] = len(notes) - 1

        #         # Lyrics
        #         lyric_elem = elem.find("lyric")
        #         if lyric_elem is not None:
        #             lyric_text = _get_required_text(lyric_elem, "text")
        #             syllabic_elem = lyric_elem.find("syllabic")
        #             if syllabic_elem is not None:
        #                 if syllabic_elem.text == "begin":
        #                     lyric_text += "-"
        #                 elif syllabic_elem.text == "middle":
        #                     lyric_text = "-" + lyric_text + "-"
        #                 elif syllabic_elem.text == "end":
        #                     lyric_text = "-" + lyric_text
        #             lyrics.append(
        #                 Lyric(time=time + position, lyric=lyric_text)
        #             )

        #         # Move time position forward if it is not in chord
        #         last_note_position = position
        #         position += round(duration * resolution / division)

        #     # Forward elements
        #     elif elem.tag == "forward":
        #         duration = int(_get_required_text(elem, "duration"))
        #         position += round(duration * resolution / division)

        #     # Backup elements
        #     elif elem.tag == "backup":
        #         duration = int(_get_required_text(elem, "duration"))
        #         position -= round(duration * resolution / division)

        time += position

        # if is_after_jump and is_fine:
        #     break

        # if not is_after_jump and (is_dacapo or is_dalsegno):
        #     measure_idx = 0
        #     is_after_jump = True
        # elif is_repeat:
        #     is_repeat = False
        #     measure_idx = last_repeat
        # else:
        #     measure_idx += 1

        measure_idx = next_measure_idx

    # Sort notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Sort tempos, key signatures, time signatures and lyrics
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))
    lyrics.sort(key=attrgetter("time"))

    if not time_signatures or time_signatures[0].time > 0:
        time_signatures.insert(
            0, TimeSignature(time=0, numerator=4, denominator=4)
        )

    return {
        "tempos": tempos,
        "key_signatures": key_signatures,
        "time_signatures": time_signatures,
        "notes": notes,
        "lyrics": lyrics,
    }


def parse_metadata(root: Element) -> Metadata:
    """Return a Metadata object parsed from a MuseScore file."""
    # Creators and copyrights
    title = None
    creators = []
    copyrights = []

    # Iterate over meta tags
    for meta_tag in root.findall("Score/metaTag"):
        name = _get_required_attr(meta_tag, "name")
        if name == "movementTitle":
            title = meta_tag.text
        # Only use 'workTitle' when movementTitle is not found
        if title is None and name == "workTitle":
            title = meta_tag.text
        if name in ("arranger", "composer", "lyricist"):
            if meta_tag.text is not None:
                creators.append(meta_tag.text)
        if name == "copyright":
            if meta_tag.text is not None:
                copyrights.append(meta_tag.text)

    return Metadata(
        title=title,
        creators=creators,
        copyright=" ".join(copyrights) if copyrights else None,
        source_format="musescore",
    )


def _get_root(path: Union[str, Path], compressed: bool = None):
    """Return root of the element tree."""
    if compressed is None:
        compressed = str(path).endswith(".mscz")

    if not compressed:
        tree = ET.parse(str(path))
        return tree.getroot()

    # Find out the main MSCX file in the compressed ZIP archive
    zip_file = ZipFile(str(path))
    if "META-INF/container.xml" not in zip_file.namelist():
        raise MuseScoreError("Container file ('container.xml') not found.")
    container = ET.fromstring(zip_file.read("META-INF/container.xml"))
    rootfile = container.find("rootfiles/rootfile")
    if rootfile is None:
        raise MuseScoreError(
            "Element 'rootfile' tag not found in the container file "
            "('container.xml')."
        )
    filename = _get_required_attr(rootfile, "full-path")
    return ET.fromstring(zip_file.read(filename))


def _get_divisions(root: Element):
    """Return a list of divisions."""
    divisions = []
    for division_elem in root.findall("Score/Division"):
        if division_elem.text is None:
            continue
        if not float(division_elem.text).is_integer():
            raise MuseScoreError(
                "Noninteger 'division' values are not supported."
            )
        divisions.append(int(division_elem.text))
    return divisions


def parse_part_elem_info(elem: Element) -> Tuple[List[str], OrderedDict]:
    """Return part information parsed from a score part element."""
    part_info: OrderedDict = OrderedDict()

    # Staff IDs
    staff_ids = [
        _get_required_attr(staff_elem, "id")
        for staff_elem in elem.findall("Staff")
    ]

    # Instrument
    instrument_elem = _get_required(elem, "Instrument")
    part_info["id"] = _get_text(instrument_elem, "instrumentId")
    part_info["name"] = _get_text(elem, "trackName", remove_newlines=True)

    # MIDI program and channel
    program_elem = instrument_elem.find("Channel/program")
    if program_elem is not None:
        program = program_elem.get("value")
        part_info["program"] = int(program) if program is not None else 0
    else:
        part_info["program"] = 0
    part_info["is_drum"] = (
        int(_get_text(instrument_elem, "Channel/midiChannel", 0)) == 10
    )

    return staff_ids, part_info


def read_musescore(
    path: Union[str, Path], resolution: int = None, compressed: bool = None
) -> Music:
    """Read a MuseScore file into a Music object.

    Parameters
    ----------
    path : str or Path
        Path to the MuseScore file to read.
    resolution : int, optional
        Time steps per quarter note. Defaults to the least common
        multiple of all divisions.
    compressed : bool, optional
        Whether it is a compressed MuseScore file. Defaults to infer
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

    # Get the score element
    score_elem = _get_required(root, "Score")

    # Meta data
    metadata = parse_metadata(root)
    metadata.source_filename = Path(path).name

    # Set resolution to the least common multiple of all divisions
    if resolution is None:
        divisions = _get_divisions(root)
        resolution = _lcm(*divisions) if divisions else 1

    # Staff information
    part_info: List[OrderedDict] = []
    staff_part_map: OrderedDict = OrderedDict()
    for part_id, part_elem in enumerate(score_elem.findall("Part")):
        staff_ids, part_elem_info = parse_part_elem_info(part_elem)
        part_info.append(part_elem_info)
        for staff_id in staff_ids:
            staff_part_map[staff_id] = part_id

    if score_elem.find("Staff") is None:
        return Music(metadata=metadata, resolution=resolution)

    # Initialize lists
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    tracks: List[Track] = []

    # Raise an error if part-list information is missing for a
    # multi-part piece
    if not part_info:
        if len(score_elem.findall("Staff")) > 1:
            raise MuseScoreError(
                "Part information is required for a multi-part piece."
            )
        staff_elem = _get_required(root, "Staff")
        instrument_info = {"program": 0, "is_drum": False}
        staff = parse_staff_elem(staff_elem, resolution, instrument_info)
    else:
        # Iterate over all staffs and measures
        for staff_elem in score_elem.findall("Staff"):
            staff_id = staff_elem.get("id")  # type: ignore
            if staff_id is None:
                if len(score_elem.findall("Staff")) > 1:
                    continue
                staff_id = next(iter(staff_part_map))
            if staff_id not in staff_part_map:
                continue

            # Parse staff
            staff = parse_staff_elem(
                staff_elem, resolution, part_info[staff_part_map[staff_id]]
            )

            # Extend lists
            tempos.extend(staff["tempos"])
            key_signatures.extend(staff["key_signatures"])
            time_signatures.extend(staff["time_signatures"])
            tracks.append(
                Track(
                    program=part_info[staff_part_map[staff_id]]["program"],
                    is_drum=part_info[staff_part_map[staff_id]]["is_drum"],
                    name=part_info[staff_part_map[staff_id]]["name"],
                    notes=staff["notes"],
                    lyrics=staff["lyrics"],
                )
            )

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
