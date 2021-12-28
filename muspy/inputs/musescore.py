"""MuseScore input interface."""
import xml.etree.ElementTree as ET
from collections import OrderedDict
from fractions import Fraction
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
from ..utils import (
    CIRCLE_OF_FIFTHS,
    MODE_CENTERS,
    NOTE_TYPE_MAP,
    TONAL_PITCH_CLASSES,
)

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
    """Return a required child element of an element.

    Raise a MuseScoreError if not found.

    """
    elem = element.find(path)
    if elem is None:
        raise MuseScoreError(
            f"Element `{path}` is required for an '{element.tag}' element."
        )
    return elem


def _get_required_attr(element: Element, attr: str) -> str:
    """Return a required attribute of an element.

    Raise a MuseScoreError if not found.

    """
    attribute = element.get(attr)
    if attribute is None:
        raise MuseScoreError(
            f"Attribute '{attr}' is required for an '{element.tag}' element."
        )
    return attribute


def _get_required_text(
    element: Element, path: str, remove_newlines: bool = False
) -> str:
    """Return a required text from a child element of an element.

    Raise a MuseScoreError otherwise.

    """
    elem = _get_required(element, path)
    if elem.text is None:
        raise MuseScoreError(
            f"Text content '{path}' of an element '{element.tag}' must not be "
            "empty."
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
    """Return the numerator and denominator of a time element."""
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


def parse_key_elem(elem: Element) -> Tuple[int, str, int, str]:
    """Return the key parsed from a key element."""
    mode = _get_text(elem, "mode", "major")
    fifths = int(_get_required_text(elem, "accidental"))
    if mode is None:
        return None, None, fifths, None
    idx = MODE_CENTERS[mode] + fifths
    if idx < 0 or idx > 20:
        return None, mode, fifths, None  # type: ignore
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + fifths]
    return root, mode, fifths, root_str


def parse_marker_measure_map(elem: Element) -> Dict[str, int]:
    """Return a marker-measure map parsed from a staff element."""
    # Initialize with a start marker
    markers: Dict[str, int] = {"start": 0}

    # Find all markers in all measures
    for i, measure_elem in enumerate(elem.findall("Measure")):
        for marker_elem in measure_elem.findall("Marker"):
            label = _get_text(marker_elem, "label")
            if label is not None:
                markers[label] = i

    return markers


def parse_meta_staff_elem(elem: Element) -> List[int]:
    """Return a list of measure indices parsed from a staff element.

    This function returns the ordering of measures, considering all
    repeats and jumps.

    """
    # Measure indices
    measure_indices = []

    # Repeats
    last_repeat = 0
    count_repeat = 1
    count_ending = 1

    # Flags
    is_after_jump = False
    is_after_play_until = False

    # Jump-related measure indices
    jump_to_idx = None
    play_until_idx = None
    continue_at_idx = None

    # Get the marker measure map
    marker_measure_map = parse_marker_measure_map(elem)

    # Iterate over all measures
    measure_idx = 0
    measure_elems = list(elem.findall("Measure"))
    while measure_idx < len(measure_elems):
        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Handle jumps
        #
        #   [Example]
        #                                jump
        #                                v
        #       ║----|----|----|----|----|----|----║
        #            ^         ^              ^
        #            jump-to   play-until     continue at
        #
        #   [Expansion]
        #
        #       ║----|----|----|----|----|               (a)
        #            ┌──────<─────<──────┘               (b)
        #            |----|----|                         (c)
        #                      └────>────>────┐          (d)
        #                                     |----║     (e)

        # (Stages b and c)
        if is_after_jump and not is_after_play_until:
            # (Stage b) Look for the jump-to measure
            if jump_to_idx is not None and measure_idx < jump_to_idx:
                # Skip the current measure if it is not the correct one
                measure_idx += 1
                continue
            # (Stage c) Look for the play-until measure
            if play_until_idx is not None and measure_idx > play_until_idx:
                # If we reach the play-until measure but no continue-at
                # measure is given, we reach the end of the score, e.g.,
                # a "D.C. al Fine" or "D.S. al Fine".
                if continue_at_idx is None:
                    break
                # Otherwise, we skip the current measure and look for
                # the continue-at measure.
                is_after_play_until = True
                measure_idx = 0
                continue
        # (Stages d and e)
        if is_after_play_until:
            # Should never enter this if statement but have it here in
            # case the file is corrupted.
            if continue_at_idx is None:
                break
            # (Stage d) Look for the continue-at measure
            if measure_idx < continue_at_idx:
                measure_idx += 1
                continue
            # (Stage e) Reset all the flags to allow another jump
            is_after_jump = False
            is_after_play_until = False
            jump_to_idx = None
            play_until_idx = None
            continue_at_idx = None

        # Set the default next measure
        next_measure_idx = measure_idx + 1

        # Jump elements
        if not is_after_jump:
            jump_elem = measure_elem.find("Jump")
            if jump_elem is not None:
                jump_to_idx = marker_measure_map.get(
                    _get_text(jump_elem, "jumpTo")
                )
                play_until_idx = marker_measure_map.get(
                    _get_text(jump_elem, "playUntil")
                )
                continue_at_idx = marker_measure_map.get(
                    _get_text(jump_elem, "continueAt")
                )
                is_after_jump = True
                # Get back to the first measure to look for the
                # jump-to measure
                next_measure_idx = 0

        # Repeat elements (forward)
        if measure_elem.find("startRepeat"):
            last_repeat = measure_idx

        # Volta elements
        is_wrong_ending = False
        for volta_elem in measure_elem.findall("voice/Spanner/Volta"):
            ending_num_text = _get_required_text(volta_elem, "endings")
            ending_num = [int(num) for num in ending_num_text.split(",")]
            # Skip this measure if it is not the correct ending
            if count_ending not in ending_num:
                is_wrong_ending = True
        # Skip this measure if it is not the correct ending
        if is_wrong_ending:
            measure_idx += 1
            continue

        # Repeat elements (backward)
        end_repeat_element = measure_elem.find("endRepeat")
        if end_repeat_element is not None:
            # Get repeat times
            if end_repeat_element.text is None:
                repeat_times = 2
            else:
                repeat_times = int(end_repeat_element.text)
            # Check if repeat times has reached
            if count_repeat < repeat_times:
                count_repeat += 1
                count_ending += 1
                next_measure_idx = last_repeat
            else:
                # Reset repeat counters
                count_repeat = 1
                count_ending = 1

        # Append the current measure index to the list to be return
        measure_indices.append(measure_idx)

        # Proceed to the next measure
        measure_idx = next_measure_idx

    return measure_indices


def parse_staff_elem(
    staff_elem: Element, resolution: int, measure_indices: List[int]
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
    measure_len = round(resolution * 4)
    # Tuples
    is_tuple = False

    # Iterate over all elements
    measure_elems = list(staff_elem.findall("Measure"))
    for measure_idx in measure_indices:
        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Get measure length
        measure_len_text = measure_elem.get("len")
        if measure_len_text is not None:
            measure_len = round(resolution * 4 * Fraction(measure_len))

        # Voice elements
        for voice_elem in measure_elem.findall("voice"):
            # Initialize position
            position = 0

            # Iterate over child elements
            for elem in voice_elem:
                # Key signatures
                if elem.tag == "KeySig":
                    root, mode, fifths, root_str = parse_key_elem(elem)
                    key_signatures.append(
                        KeySignature(
                            time=time + position,
                            root=root,
                            mode=mode,
                            fifths=fifths,
                            root_str=root_str,
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
                        float(_get_text(elem, "velocity", velocity))
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

                # Rest elements
                if elem.tag == "Rest":
                    # Move time position forward if it is a rest
                    duration_type = _get_required_text(elem, "durationType")
                    if duration_type == "measure":
                        duration_text = _get_text(elem, "duration")
                        if duration_text is not None:
                            duration = (
                                resolution * 4 * float(Fraction(duration_text))
                            )
                        else:
                            duration = measure_len
                        position += round(duration)
                        continue
                    duration = NOTE_TYPE_MAP[duration_type] * resolution
                    position += round(duration)
                    continue

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

                    # Grace notes
                    is_grace = False
                    for child in elem:
                        if "grace" in child.tag or child.tag in (
                            "appoggiatura",
                            "acciaccatura",
                        ):
                            is_grace = True

                    # Check if it is a tied chord
                    is_outgoing_tie = False
                    for spanner_elem in elem.findall("Spanner"):
                        if (
                            spanner_elem.get("type") == "Tie"
                            and spanner_elem.find("next/location") is not None
                        ):
                            is_outgoing_tie = True

                    # Collect notes
                    for note_elem in elem.findall("Note"):
                        # Get pitch
                        pitch = int(_get_required_text(note_elem, "pitch"))
                        pitch_str = TONAL_PITCH_CLASSES[
                            int(_get_required_text(note_elem, "tpc"))
                        ]

                        # Handle grace note
                        if is_grace:
                            # Append a new note to the note list
                            notes.append(
                                Note(
                                    time=time + position,
                                    pitch=pitch,
                                    duration=duration,
                                    velocity=velocity,
                                    pitch_str=pitch_str,
                                )
                            )
                            continue

                        # Check if it is a tied note
                        for spanner_elem in note_elem.findall("Spanner"):
                            if (
                                spanner_elem.get("type") == "Tie"
                                and spanner_elem.find("next/location")
                                is not None
                            ):
                                is_outgoing_tie = True

                        # Check if it is an incoming tied note
                        if pitch in ties:
                            note_idx = ties[pitch]
                            notes[note_idx].duration += duration

                            if is_outgoing_tie:
                                ties[pitch] = note_idx
                            else:
                                del ties[pitch]

                        else:
                            # Append a new note to the note list
                            notes.append(
                                Note(
                                    time=time + position,
                                    pitch=pitch,
                                    duration=duration,
                                    velocity=velocity,
                                    pitch_str=pitch_str,
                                )
                            )

                        if is_outgoing_tie:
                            ties[pitch] = len(notes) - 1

                    # Lyrics
                    lyric_elem = elem.find("lyrics")
                    if lyric_elem is not None:
                        lyric_text = _get_required_text(
                            lyric_elem, "text", remove_newlines=True
                        )
                        lyrics.append(
                            Lyric(time=time + position, lyric=lyric_text)
                        )

                    if not is_grace:
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
                        # notes[-1].duration = new_duration
                        position += int(new_duration - duration)
                    is_tuple = False

        time += position

    # Sort notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

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

    # Get the meta staff, assuming the first staff
    meta_staff_elem = score_elem.find("Staff")
    if meta_staff_elem is not None:
        # Parse measure ordering from the meta staff, expanding all
        # repeats and jumps
        measure_indices = parse_meta_staff_elem(meta_staff_elem)

        # Raise an error if part-list information is missing
        if not part_info:
            raise MuseScoreError("Part information is missing.")

        # Iterate over all staffs
        part_track_map: Dict[int, int] = {}
        for staff_elem in score_elem.findall("Staff"):
            staff_id = staff_elem.get("id")  # type: ignore
            if staff_id is None:
                if len(score_elem.findall("Staff")) > 1:
                    continue
                staff_id = next(iter(staff_part_map))
            if staff_id not in staff_part_map:
                continue

            # Parse the staff
            staff = parse_staff_elem(staff_elem, resolution, measure_indices)

            # Extend lists
            tempos.extend(staff["tempos"])
            key_signatures.extend(staff["key_signatures"])
            time_signatures.extend(staff["time_signatures"])
            part_id = staff_part_map[staff_id]
            if part_id in part_track_map:
                track_id = part_track_map[part_id]
                tracks[track_id].notes.extend(staff["notes"])
                tracks[track_id].lyrics.extend(staff["lyrics"])
            else:
                part_track_map[part_id] = len(tracks)
                tracks.append(
                    Track(
                        program=part_info[part_id]["program"],
                        is_drum=part_info[part_id]["is_drum"],
                        name=part_info[part_id]["name"],
                        notes=staff["notes"],
                        lyrics=staff["lyrics"],
                    )
                )

        # Sort tempos, key signatures and time signatures
        tempos.sort(key=attrgetter("time"))
        key_signatures.sort(key=attrgetter("time"))
        time_signatures.sort(key=attrgetter("time"))

        # Sort notes and lyrics
        for track in tracks:
            track.notes.sort(
                key=attrgetter("time", "pitch", "duration", "velocity")
            )
            track.lyrics.sort(key=attrgetter("time"))

    return Music(
        metadata=metadata,
        resolution=resolution,
        tempos=tempos,
        key_signatures=key_signatures,
        time_signatures=time_signatures,
        tracks=tracks,
    )
