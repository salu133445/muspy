"""MuseScore input interface."""
import time
import warnings
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from fractions import Fraction
from functools import reduce
from operator import attrgetter
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Tuple, TypeVar, Union
from xml.etree.ElementTree import Element
from zipfile import ZipFile

from ..classes import (
    Barline,
    Beat,
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
from .musicxml import get_beats

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
    beats = _get_text(elem, "sigN")
    if beats is None:
        beats = _get_text(elem, "nom1")
    if beats is None:
        raise MuseScoreError(
            "Neither 'sigN' nor 'nom1' element is found for a TimeSig element."
        )
    if "+" in beats:
        numerator = sum(int(beat) for beat in beats.split("+"))
    else:
        numerator = int(beats)

    # Denominator
    beat_type = _get_text(elem, "sigD")
    if beat_type is None:
        beat_type = _get_text(elem, "den")
    if beat_type is None:
        raise MuseScoreError(
            "Neither 'sigD' nor 'den' element is found for a TimeSig element."
        )
    if "+" in beat_type:
        raise RuntimeError(
            "Compound time signatures with separate fractions "
            "are not supported."
        )
    denominator = int(beat_type)

    return numerator, denominator


def parse_key_elem(elem: Element) -> Tuple[int, str, int, str]:
    """Return the key parsed from a key element."""
    mode = _get_text(elem, "mode")
    fifths_text = _get_text(elem, "accidental")  # MuseScore 2.x and 3.x
    if fifths_text is None:
        fifths_text = _get_text(elem, "subtype")  # MuseScore 1.x
    if fifths_text is None:
        raise MuseScoreError(
            "Neither 'accidental' nor 'subtype' element is found for a KeySig "
            "element."
        )
    fifths = int(fifths_text)
    if mode is None:
        return None, None, fifths, None
    idx = MODE_CENTERS[mode] + fifths
    if idx < 0 or idx > 20:
        return None, mode, fifths, None  # type: ignore
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + fifths]
    return root, mode, fifths, root_str


def parse_lyric_elem(elem: Element) -> str:
    """Return the lyric text parsed from a lyric element."""
    text = _get_required_text(elem, "text")
    syllabic_elem = elem.find("syllabic")
    if syllabic_elem is not None:
        if syllabic_elem.text == "begin":
            text = f"{text} -"
        elif syllabic_elem.text == "middle":
            text = f"- {text} -"
        elif syllabic_elem.text == "end":
            text = f"- {text}"
    return text


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


def get_measure_ordering(elem: Element, timeout: int = None) -> List[int]:
    """Return a list of measure indices parsed from a staff element.

    This function returns the ordering of measures, considering all
    repeats and jumps.

    """
    # Measure indices
    measure_indices = []

    # Repeats
    last_repeat = 0
    count_repeat: DefaultDict[int, int] = defaultdict(lambda: 1)
    count_ending = 1

    # Flags
    is_after_repeat = False
    is_after_jump = False
    is_after_play_until = False
    is_repeat_done: DefaultDict[int, bool] = defaultdict(lambda: False)
    is_jump_done: DefaultDict[int, bool] = defaultdict(lambda: False)

    # Jump-related measure indices
    jump_to_idx = None
    play_until_idx = None
    continue_at_idx = None

    # Get the marker measure map
    marker_measure_map = parse_marker_measure_map(elem)

    # Record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # Iterate over all measures
    measure_idx = 0
    measure_elems = list(elem.findall("Measure"))
    while measure_idx < len(measure_elems):

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(
                f"Abort the process as it runned over {timeout} seconds."
            )

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
        if not is_jump_done[measure_idx] and not is_after_jump:
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
                # Set flaps
                is_after_jump = True
                is_jump_done[measure_idx] = True
                # Get back to the first measure to look for the
                # jump-to measure
                next_measure_idx = 0

        # Repeat elements (forward)
        if measure_elem.find("startRepeat") is not None:
            last_repeat = measure_idx
            # Reset repeat counters
            if not is_after_repeat:
                count_repeat[measure_idx] = 1
                count_ending = 1

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
            # Reset the flag
            is_after_repeat = False
            continue

        # Repeat elements (backward)
        if not is_after_jump:
            end_repeat_element = measure_elem.find("endRepeat")
            if end_repeat_element is not None:
                # Get repeat times
                if end_repeat_element.text is None:
                    repeat_times = 2
                else:
                    repeat_times = int(end_repeat_element.text)
                # Check if repeat times has reached
                if (
                    not is_repeat_done[measure_idx]
                    and count_repeat[measure_idx] < repeat_times
                ):
                    is_after_repeat = True
                    count_repeat[measure_idx] += 1
                    count_ending += 1
                    next_measure_idx = last_repeat
                else:
                    # Reset the repeat counter
                    is_after_repeat = False
                    is_repeat_done[measure_idx] = True
                    count_repeat[measure_idx] = 1
                    count_ending = 1

        # Append the current measure index to the list to be return
        measure_indices.append(measure_idx)

        # Proceed to the next measure
        measure_idx = next_measure_idx

    return measure_indices


def parse_meta_staff_elem(
    staff_elem: Element,
    resolution: int,
    measure_indices: List[int],
    timeout: int = None,
) -> Tuple[
    List[Tempo],
    List[KeySignature],
    List[TimeSignature],
    List[Barline],
    List[Beat],
]:
    """Return data parsed from a meta staff element.

    This function only parses the tempos, key and time signatures. Use
    `parse_staff_elem` to parse the notes and lyrics.

    """
    # Initialize lists
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    barlines: List[Barline] = []

    # Initialize variables
    time_ = 0
    measure_len = round(resolution * 4)
    is_tuple = False
    downbeat_times: List[int] = []

    # Record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # Iterate over all elements
    measure_elems = list(staff_elem.findall("Measure"))
    for measure_idx in measure_indices:

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(
                f"Abort the process as it runned over {timeout} seconds."
            )

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Barlines
        barlines.append(Barline(time=time_))

        # Collect the measure start times
        downbeat_times.append(time_)

        # Get measure length
        measure_len_text = measure_elem.get("len")
        if measure_len_text is not None:
            measure_len = round(resolution * 4 * Fraction(measure_len_text))

        # Initialize position
        position = 0

        # Get voice elements
        voice_elems = list(measure_elem.findall("voice"))  # MuseScore 3.x
        if not voice_elems:
            voice_elems = [measure_elem]  # MuseScore 1.x and 2.x

        # Iterate over voice elements
        for voice_elem in voice_elems:
            # Reset position
            position = 0

            # Iterate over child elements
            for elem in voice_elem:

                # Key signatures
                if elem.tag == "KeySig":
                    root, mode, fifths, root_str = parse_key_elem(elem)
                    key_signatures.append(
                        KeySignature(
                            time=time_ + position,
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
                            time=time_ + position,
                            numerator=numerator,
                            denominator=denominator,
                        )
                    )

                # Tempo elements
                if elem.tag == "Tempo":
                    tempos.append(
                        Tempo(
                            time_ + position,
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
                    if duration != new_duration:
                        position += int(new_duration - duration)
                    is_tuple = False

        time_ += position

    # Sort tempos, key and time signatures
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))

    # Get the beats
    beats = get_beats(
        downbeat_times, time_signatures, resolution, is_sorted=True
    )

    return tempos, key_signatures, time_signatures, barlines, beats


def parse_staff_elem(
    staff_elem: Element,
    resolution: int,
    measure_indices: List[int],
    timeout: int = None,
) -> Tuple[List[Note], List[Lyric]]:
    """Return notes and lyrics parsed from a staff element.

    This function only parses the notes and lyrics. Use
    `parse_meta_staff_elem` to parse the tempos, key and time
    signatures.

    """
    # Initialize lists
    notes: List[Note] = []
    lyrics: List[Lyric] = []

    # Initialize variables
    time_ = 0
    velocity = 64
    measure_len = round(resolution * 4)
    is_tuple = False

    # Record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # Create a dictionary to handle ties
    ties: Dict[int, int] = {}

    # Iterate over all elements
    measure_elems = list(staff_elem.findall("Measure"))
    for measure_idx in measure_indices:

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(
                f"Abort the process as it runned over {timeout} seconds."
            )

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Get measure length
        measure_len_text = measure_elem.get("len")
        if measure_len_text is not None:
            measure_len = round(resolution * 4 * Fraction(measure_len_text))

        # Initialize position
        position = 0

        # Get voice elements
        voice_elems = list(measure_elem.findall("voice"))  # MuseScore 3.x
        if not voice_elems:
            voice_elems = [measure_elem]  # MuseScore 1.x and 2.x

        # Iterate over voice elements
        for voice_elem in voice_elems:
            # Initialize position
            position = 0

            # Iterate over child elements
            for elem in voice_elem:

                # Dynamic elements
                if elem.tag == "Dynamic":
                    velocity = round(
                        float(_get_text(elem, "velocity", velocity))
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
                                    time=time_ + position,
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
                                    time=time_ + position,
                                    pitch=pitch,
                                    duration=duration,
                                    velocity=velocity,
                                    pitch_str=pitch_str,
                                )
                            )

                        if is_outgoing_tie:
                            ties[pitch] = len(notes) - 1

                    # Lyrics
                    lyric_elem = elem.find("Lyrics")
                    if lyric_elem is not None:
                        lyric_text = parse_lyric_elem(lyric_elem)
                        lyrics.append(
                            Lyric(time=time_ + position, lyric=lyric_text)
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
                        notes[-1].duration = new_duration
                        position += int(new_duration - duration)
                    is_tuple = False

        time_ += position

    # Sort notes
    notes.sort(key=attrgetter("time", "pitch", "duration", "velocity"))

    # Sort lyrics
    lyrics.sort(key=attrgetter("time"))

    return notes, lyrics


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


def parse_part_elem_info(
    elem: Element, has_staff_id: bool = True
) -> Tuple[Optional[List[str]], OrderedDict]:
    """Return part information parsed from a score part element."""
    part_info: OrderedDict = OrderedDict()

    # Staff IDs
    if has_staff_id:
        staff_ids = [
            _get_required_attr(staff_elem, "id")
            for staff_elem in elem.findall("Staff")
        ]  # MuseScore 2.x and 3.x
    else:
        staff_ids = None  # MuseScore 1.x

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
    path: Union[str, Path],
    resolution: int = None,
    compressed: bool = None,
    timeout: int = None,
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

    Warnings
    --------
    This function is based on MuseScore 3. Files created by an earlier
    version of MuseScore might not be read correctly.

    """
    # Get element tree root
    root = _get_root(path, compressed)

    # Detect MuseScore version
    musescore_version = root.get("version")
    if not musescore_version.startswith("3."):
        warnings.warn(
            f"Detected a legacy MuseScore version of {musescore_version}. "
            "Data might not be loaded correctly.",
            MuseScoreWarning,
        )

    # Get the score element
    score_elem = root.find("Score")  # MuseScore 3.x
    if score_elem is None:
        score_elem = root  # MuseScore 1.x and 2.x

    # Meta data
    metadata = parse_metadata(root)
    metadata.source_filename = Path(path).name

    # Set resolution to the least common multiple of all divisions
    if resolution is None:
        divisions = _get_divisions(root)
        resolution = _lcm(*divisions) if divisions else 1

    # Detect if has staff id is available
    has_staff_id = True
    first_staff_elem = score_elem.find("part/Staff")
    if first_staff_elem is None or first_staff_elem.get("id") is None:
        has_staff_id = False

    # Staff information
    part_info: List[OrderedDict] = []
    staff_part_map: OrderedDict = OrderedDict()
    staff_id = 1
    for part_id, part_elem in enumerate(score_elem.findall("Part")):
        staff_ids, part_elem_info = parse_part_elem_info(
            part_elem, has_staff_id
        )
        part_info.append(part_elem_info)
        if has_staff_id:  # MuseScore 2.x and 3.x
            for staff_id in staff_ids:  # type: ignore
                staff_part_map[staff_id] = part_id
        else:  # MuseScore 1.x
            for _ in range(len(part_elem.findall("Staff"))):
                staff_part_map[str(staff_id)] = part_id
                staff_id += 1

    # Raise an error if part-list information is missing
    if not part_info:
        raise MuseScoreError("Part information is missing.")

    # Get the meta staff, assuming the first staff
    meta_staff_elem = score_elem.find("Staff")

    # Return empty music object with metadata if no staff is found
    if meta_staff_elem is None:
        return Music(metadata=metadata, resolution=resolution)

    # Parse measure ordering from the meta staff, expanding all repeats
    # and jumps
    measure_indices = get_measure_ordering(meta_staff_elem, timeout)

    # Parse the meta part element
    (
        tempos,
        key_signatures,
        time_signatures,
        barlines,
        beats,
    ) = parse_meta_staff_elem(
        meta_staff_elem, resolution, measure_indices, timeout
    )

    # Initialize lists
    tracks: List[Track] = []

    # Record start time to check for timeout
    start_time = time.time()

    # Iterate over all staffs
    part_track_map: Dict[int, int] = {}
    for staff_elem in score_elem.findall("Staff"):
        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(
                f"Abort the process as it runned over {timeout} seconds."
            )

        # Get the staff ID
        staff_id = staff_elem.get("id")  # type: ignore
        if staff_id is None:
            if len(score_elem.findall("Staff")) > 1:
                continue
            staff_id = next(iter(staff_part_map))
        if staff_id not in staff_part_map:
            continue

        # Parse the staff
        notes, lyrics = parse_staff_elem(
            staff_elem, resolution, measure_indices, timeout
        )

        # Extend lists
        part_id = staff_part_map[staff_id]
        if part_id in part_track_map:
            track_id = part_track_map[part_id]
            tracks[track_id].notes.extend(notes)
            tracks[track_id].lyrics.extend(lyrics)
        else:
            part_track_map[part_id] = len(tracks)
            tracks.append(
                Track(
                    program=part_info[part_id]["program"],
                    is_drum=part_info[part_id]["is_drum"],
                    name=part_info[part_id]["name"],
                    notes=notes,
                    lyrics=lyrics,
                )
            )

    # Make sure everything is sorted
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))
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
        barlines=barlines,
        beats=beats,
        tracks=tracks,
    )
