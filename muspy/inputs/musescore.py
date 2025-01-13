"""MuseScore input interface."""
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from fractions import Fraction
from functools import reduce
from operator import attrgetter
from os.path import basename
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar, Union
from xml.etree.ElementTree import Element
from zipfile import ZipFile
from re import sub
from copy import deepcopy
import numpy as np
import warnings

from ..classes import *
from ..annotations import *
from ..music import Music, DEFAULT_RESOLUTION
from ..utils import (
    CIRCLE_OF_FIFTHS,
    MODE_CENTERS,
    NOTE_TYPE_MAP,
    TONAL_PITCH_CLASSES
)

T = TypeVar("T")

# number of octaves to shift from an ottava
OTTAVA_OCTAVE_SHIFT_FACTORS = {8: 1, 15: 2, 22: 3}
# OTTAVA_N_OCTAVE_SHIFTS = {
#     "22mb": -3, "15mb": -2, "8vb": -1,
#     "8va": 1, "15ma": 2, "22ma": 3,
# }
# OTTAVA_PITCH_SHIFTS = {key: value * 12 for key, value in OTTAVA_N_OCTAVE_SHIFTS.items()} # switch from octave shifts to pitch shifts

# transposing to concert key for tuned instruments
TRANSPOSE_CHROMATIC_TO_CIRCLE_OF_FIFTHS_STEPS = {-i: ((-i) if (i % 2 == 0) else ((-i + 6) % -12)) for i in range(12)}

# subtypes of arpeggios
ARPEGGIO_SUBTYPES = ["default", "up", "down", "bracket", "up straight", "down straight"]

# subtypes of chord lines
CHORDLINE_SUBTYPES = ["fall", "doit", "plop", "scoop", "slide out down", "slide out up", "slide in above", "slide in below"]

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


def prettify_ET(root: ET, output_filepath: str = None): # prettify an xml element tree
    """Return a pretty-printed (or outputted) XML string for the Element `root`.
    """
    rough_string = ET.tostring(element = root, encoding = "utf-8") # get string for xml
    rough_string = str(rough_string, "UTF-8") # convert from type bytes to str
    if output_filepath:
        with open(output_filepath, "w") as file:
            file.write(rough_string)
    else:
        print(rough_string)


def _get_required(element: Element, path: str) -> Element:
    """Return a required child element of an element.

    Raise a MuseScoreError if not found.

    """
    elem = element.find(path = path)
    if elem is None:
        raise MuseScoreError(f"Element `{path}` is required for an '{element.tag}' element.")
    return elem


def _get_required_attr(element: Element, attr: str) -> str:
    """Return a required attribute of an element.

    Raise a MuseScoreError if not found.

    """
    attribute = element.get(attr)
    if attribute is None:
        raise MuseScoreError(f"Attribute '{attr}' is required for an '{element.tag}' element.")
    return attribute


def _get_required_text(element: Element, path: str, remove_newlines: bool = False) -> str:
    """Return a required text from a child element of an element.

    Raise a MuseScoreError otherwise.

    """
    elem = _get_required(element = element, path = path)
    if elem.text is None:
        return ""
        # raise MuseScoreError(f"Text content '{path}' of an element '{element.tag}' must not be empty.")
    if remove_newlines:
        return " ".join(elem.text.splitlines())
    return elem.text


def _get_raw_text(element: Element, path: str = "text") -> str:
    """Returns the raw XML-level text in an element"""

    # find the element
    elem = element.find(path = path)

    # if that element is not found
    if elem is None:
        return None

    # wrangle the raw string
    text = str(ET.tostring(element = elem, encoding = "utf-8"), encoding = "UTF-8").strip()
    path = basename(path) if "/" in path else path
    text = sub(pattern = f"<{path}>|</{path}>|<font face=\"Edwin\" />", repl = "", string = text)
    return text


def _get_root(path: Union[str, Path], compressed: bool = None):
    """Return root of the element tree."""
    path = str(path) # ensure path is a string

    if compressed is None:
        compressed = path.endswith(".mscz")

    if not compressed:
        tree = ET.parse(path)
        return tree.getroot()

    # Find out the main MSCX file in the compressed ZIP archive
    try:
        zip_file = ZipFile(file = path)
    except: # zipfile.BadZipFile: File is not a zip file
        raise MuseScoreError(f"{path} is not a zip file")
    if "META-INF/container.xml" not in zip_file.namelist():
        raise MuseScoreError("Container file ('container.xml') not found.")
    container = ET.fromstring(zip_file.read("META-INF/container.xml")) # read the container file as xml elementtree
    rootfile = container.findall(path = "rootfiles/rootfile") # find all branches in the container file, look for .mscx
    rootfile = [file for file in rootfile if "mscx" in file.get("full-path")]
    if len(rootfile) == 0:
        raise MuseScoreError("Element 'rootfile' tag not found in the container file ('container.xml').")
    filename = _get_required_attr(element = rootfile[0], attr = "full-path")
    if filename in zip_file.namelist():
        root = ET.fromstring(zip_file.read(filename))
    else:
        try:
            root = ET.fromstring(zip_file.read(tuple(path for path in zip_file.namelist() if path.endswith(".mscx"))[0]))
        except (IndexError):
            raise MuseScoreError("No .mscx file could be found in .mscz.")
    return root


def _get_divisions(root: Element) -> List[int]:
    """Return a list of divisions."""
    divisions = []
    for division in root.findall(path = "Division"):
        if division.text is None:
            continue
        if not float(division.text).is_integer():
            raise MuseScoreError(
                "Noninteger 'division' values are not supported."
            )
        divisions.append(int(division.text))
    return divisions


def parse_repeats(elem: Element) -> Tuple[list, list]:
    """Read repeats."""
    # Initialize with a start marker
    start_repeats = [0]
    end_repeats = [[],]

    # Find all repeats in all measures
    for i, measure in enumerate(elem.findall(path = "Measure")):
        # check for startRepeat
        if measure.find(path = "startRepeat") is not None:
            start_repeats.append(i)
            end_repeats.append([])
        # check for endRepeat
        if measure.find(path = "endRepeat") is not None:
            repeat_times = max(int(_get_text(element = measure, path = "endRepeat", default = 2)), 2) - 1 # default is 2 because by default, a repeat causes a section to be played twice
            end_repeats[len(start_repeats) - 1].extend([i] * repeat_times)

    # if there is an implied repeat at the end
    if len(end_repeats[-1]) == 0 and len(start_repeats) >= 2:
        end_repeats[-1] = [i]

    # remove faulty repeats (start repeats with no corresponding end repeats)
    start_repeats_filtered, end_repeats_filtered = [], []
    for i in range(len(end_repeats)):
        if len(end_repeats[i]) > 0:
            start_repeats_filtered.append(start_repeats[i])
            end_repeats_filtered.append(end_repeats[i])

    return start_repeats_filtered, end_repeats_filtered


def parse_markers(elem: Element) -> Dict[str, int]:
    """Return a marker-measure map parsed from a staff element."""
    # Initialize with a start marker
    markers: Dict[str, int] = {"start": 0}

    # Find all markers in all measures
    for i, measure in enumerate(elem.findall(path = "Measure")):
        for marker in measure.findall(path = "Marker"):
            label = _get_text(element = marker, path = "label")
            if label is not None:
                markers[label] = i

    return markers


def get_measure_ordering(elem: Element, timeout: int = None) -> List[int]:
    """Return a list of measure indices parsed from a staff element.

    This function returns the ordering of measures, considering all
    repeats and jumps.

    """
    # create measure indices list
    measure_indicies = []

    # Get the markers and repeats
    markers = parse_markers(elem = elem)
    start_repeats, end_repeats = parse_repeats(elem = elem)
    voltas_encountered = [] # voltas that have been past already
    current_repeat_idx = -1
    current_end_repeat_idx = 0

    # Record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # boolean flags
    before_jump = True
    add_current_measure_idx = True

    # jump related indicies
    jump_to_idx = None
    play_until_idx = None
    continue_at_idx = None

    # Iterate over all measures
    measures = elem.findall(path = "Measure")
    measure_idx = 0
    while measure_idx < len(measures):

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"Abort the process as it runned over {timeout} seconds.")

        # Get the measure element
        measure = measures[measure_idx]

        #                                jump
        #                                v
        #       ║----|----|----|----|----|----|----║
        #            ^         ^              ^
        #            jump-to   play-until     continue at

        # set default next measure id
        next_measure_idx = measure_idx + 1

        # look for start repeat
        if measure_idx in start_repeats: # if this measure is the start of a repeat section
            previous_repeat_idx = current_repeat_idx
            current_repeat_idx = start_repeats.index(measure_idx)
            if previous_repeat_idx != current_repeat_idx:
                current_end_repeat_idx = 0

        # look for jump
        jump = measure.find(path = "Jump") # search for jump element
        if jump is not None and before_jump: # if jump is found
            # set jump related indicies
            jump_to_idx = markers.get(_get_text(element = jump, path = "jumpTo"))
            play_until_idx = markers.get(_get_text(element = jump, path = "playUntil"))
            continue_at_idx = markers.get(_get_text(element = jump, path = "continueAt"))
            # set boolean flags
            before_jump = False
            # reset some variables
            voltas_encountered = []
            # go to the jump to measure
            next_measure_idx = jump_to_idx

        # look for end repeat (if there are any)
        if len(end_repeats) > 0:
            if current_end_repeat_idx < len(end_repeats[current_repeat_idx]) and measure_idx == end_repeats[current_repeat_idx][current_end_repeat_idx]: # if there is an end repeat to look out for (still an outstanding end_repeat) and we are at the end repeat
                next_measure_idx = start_repeats[current_repeat_idx]
                current_end_repeat_idx += 1

        # look for first, second, etc. endings
        volta = measure.find(path = "voice/Spanner/Volta/..") # select the parent element
        if volta is not None:
            if measure_idx not in (encounter[0] for encounter in voltas_encountered):
                volta_duration = _get_text(element = volta, path = "next/location/measures")
                if volta_duration is not None:
                    voltas_encountered.append((measure_idx, int(volta_duration)))
            else: # if we have already seen this volta, skip volta_duration measures ahead
                for volta_duration in (encounter[1] for encounter in voltas_encountered if encounter[0] >= measure_idx):
                    measure_idx += volta_duration
                next_measure_idx = measure_idx
                add_current_measure_idx = False

        # look for Coda / Fine markings
        if not before_jump and measure_idx == play_until_idx:
            if continue_at_idx: # Coda
                next_measure_idx = continue_at_idx
            else: # Fine
                next_measure_idx = len(measures) # end the while loop at the end of this iteration

        # add the current measure index to measure indicies if I am allowed to
        if add_current_measure_idx:
            measure_indicies.append(measure_idx)
            # for debugging
            # print(measure_idx + 1, end = " " if measure_idx + 1 == next_measure_idx else "\n")
        else: # flick off the switch
            add_current_measure_idx = True

        # Proceed to the next measure
        measure_idx = next_measure_idx

    return measure_indicies


def get_improved_measure_ordering(measures: List[Element], measure_indicies: List[int]) -> List[int]:
    """Return a list of measure indices parsed from a staff element.

    This function returns the ordering of measures, considering all
    repeats and jumps, as well as part-specific repeats.

    """

    # scrape measures for repeat counts
    measure_repeat_counts = [0] * len(measure_indicies)
    for i, measure_idx in enumerate(measure_indicies): # MuseScore 3.x default
        measure = measures[measure_idx] # get the measure element
        measure_repeat_count = _get_text(element = measure, path = "measureRepeatCount") # check if this measure is a repeat
        if measure_repeat_count is not None:
            measure_repeat_counts[i] = int(measure_repeat_count)
    if sum(measure_repeat_counts) == 0: # MuseScore 1.x and 2.x
        for i, measure_idx in enumerate(measure_indicies): # MuseScore 3.x default
            measure = measures[measure_idx] # get the measure element
            if measure.find(path = "voice/RepeatMeasure") is not None:
                measure_repeat_counts[i] = 1

    # chunk into blocks
    i = len(measure_repeat_counts) - 1
    while i >= 0:
        if measure_repeat_counts[i] > 1:
            measure_repeat_counts[(i + 1 - measure_repeat_counts[i]):(i + 1)] = [measure_repeat_counts[i]] * measure_repeat_counts[i]
            i -= measure_repeat_counts[i]
        else:
            i -= 1
    del i

    # get improved measure indicies
    measure_indicies_improved = [0] * len(measure_indicies)
    for i in range(len(measure_indicies)):
        j = i
        while measure_repeat_counts[j] > 0:
            j -= measure_repeat_counts[j]
            if j < 0: # if j becomes an invalid index
                j = 0 # set j to 0
                break # break out of while loop
        measure_indicies_improved[i] = measure_indicies[j]

    # return improved measure indicies
    return measure_indicies_improved


def print_measure_indicies(measure_indicies: List[int]):
    """Print the measure indicies in a readable way (new line for every jump)"""

    # convert into measure numbers as opposed to indicies
    measure_indicies = [measure_idx + 1 for measure_idx in measure_indicies]

    # create empty output
    measure_indicies_formatted = ["",] * len(measure_indicies)
    for i in range(len(measure_indicies) - 1):
        if measure_indicies[i] + 1 == measure_indicies[i + 1]:
            measure_indicies_formatted[i] = f"{measure_indicies[i]} "
        else:
            measure_indicies_formatted[i] = f"{measure_indicies[i]}\n"
    measure_indicies_formatted[-1] = str(measure_indicies[-1])

    # print output
    print(*measure_indicies_formatted, sep = "", end = "\n")


def get_beats(downbeat_times: List[int], time_signatures: List[TimeSignature], resolution: int = DEFAULT_RESOLUTION, is_sorted: bool = False) -> List[Beat]:
    """Return beats given downbeat positions and time signatures.

    Parameters
    ----------
    downbeat_times : sequence of int
        Positions of the downbeats.
    time_signatures : sequence of :class:`muspy.TimeSignature`
        Time signature objects.
    resolution : int, default: `muspy.DEFAULT_RESOLUTION` (24)
        Time steps per quarter note.
    is_sorted : bool, default: False
        Whether the downbeat times and time signatures are sorted.

    Returns
    -------
    list of :class:`read_musescore.Beat`
        Computed beats.

    """

    # Return a list of downbeats if no time signatures is given
    if not time_signatures:
        return [Beat(time = int(round(time)), is_downbeat = True) for time in downbeat_times]

    # Sort the downbeats and time signatures if necessary
    if not is_sorted:
        downbeat_times = sorted(downbeat_times)
        time_signatures = sorted(time_signatures, key = attrgetter("time"))

    # Compute the beats
    beats: List[Beat] = []
    sign_idx = 0
    downbeat_idx = 0
    while downbeat_idx < len(downbeat_times):
        # Select the correct time signatures
        if sign_idx + 1 < len(time_signatures) and downbeat_times[downbeat_idx] < time_signatures[sign_idx + 1].time:
            sign_idx += 1
            continue

        # Set time signature
        time_sign = time_signatures[sign_idx]
        beat_resolution = resolution / (time_sign.denominator / 4)

        # Get the next downbeat
        if downbeat_idx < len(downbeat_times) - 1:
            end: float = downbeat_times[downbeat_idx + 1]
        else:
            end = downbeat_times[downbeat_idx] + (beat_resolution * time_sign.numerator)

        # Append the downbeat
        start = int(round(downbeat_times[downbeat_idx]))
        beats.append(Beat(time = start, is_downbeat = True))

        # Append beats
        beat_times = np.arange(start = start + beat_resolution, stop = end, step = beat_resolution)
        for time in beat_times:
            beats.append(Beat(time = int(round(time)), is_downbeat = False))

        downbeat_idx += 1

    return beats


def parse_metadata(root: Element) -> Metadata:
    """Return a Metadata object parsed from a MuseScore file."""
    # creators and copyrights
    title, subtitle = None, None
    creators = []
    copyrights = []

    # iterate over meta tags
    for meta_tag in root.findall(path = "Score/metaTag"):
        name = _get_required_attr(element = meta_tag, attr = "name")
        if name == "movementTitle":
            title = meta_tag.text
        if name == "subtitle":
            subtitle = meta_tag.text
        # Only use 'workTitle' when movementTitle is not found
        if title is None and name == "workTitle":
            title = meta_tag.text
        if name in ("arranger", "composer", "lyricist"):
            if meta_tag.text is not None:
                creators.append(meta_tag.text)
        if name == "copyright":
            if meta_tag.text is not None:
                copyrights.append(meta_tag.text)

    return Metadata(title = title, subtitle = subtitle, creators = creators, copyright = " ".join(copyrights) if copyrights else None, source_format = "musescore")


def parse_part_info(elem: Element, musescore_version: int) -> Tuple[Optional[List[str]], OrderedDict]:
    """Return part information parsed from a score part element."""
    part_info: OrderedDict = OrderedDict()

    # Staff IDs
    staffs = elem.findall(path = "Staff")
    if musescore_version >= 2:
        staff_ids = [_get_required_attr(element = staff, attr = "id") for staff in staffs]
    else: # MuseScore 1
        staff_ids = list(range(1, len(staffs) + 1))  # MuseScore 1.x

    # Instrument
    instrument = _get_required(element = elem, path = "Instrument")
    part_info["id"] = _get_text(element = instrument, path = "instrumentId", remove_newlines = True)
    part_info["name"] = _get_text(element = elem, path = "trackName", remove_newlines = True)
    part_info["transposeChromatic"] = int(_get_text(element = instrument, path = "transposeChromatic", remove_newlines = True, default = "0"))

    # MIDI program and channel
    program = instrument.find(path = "Channel/program")
    if program is not None:
        program = program.get("value")
        part_info["program"] = int(program) if program is not None else 0
    else:
        part_info["program"] = 0
    part_info["is_drum"] = ((int(_get_text(element = instrument, path = "Channel/midiChannel", default = 0)) == 9) or
                            (_get_text(element = instrument, path = "clef", default = "") == "PERC") or
                            ("drum" in str(part_info["name"]).lower()) or
                            (len(instrument.findall(path = "Drum")) > 0))

    return staff_ids, part_info


def get_part_staff_info(elem: Element, musescore_version: int) -> Tuple[List[OrderedDict], OrderedDict]:
    """Return part information and the mappings between staff and parts from a list of all the parts elements."""

    # initialize return collections
    parts_info: List[OrderedDict] = [] # for storing info on each part
    staff_part_map: OrderedDict = OrderedDict() # for connecting staff ids (keys) to the part they belong to (values)

    # iterate through the parts
    for part_id, part in enumerate(elem):

        # get part info
        staff_ids, current_part_info = parse_part_info(elem = part, musescore_version = musescore_version) # get the part info
        parts_info.append(current_part_info) # add the current part info to parts_info

        # Deal with quirks of MuseScore 1
        if musescore_version < 2:
            current_max_staff_id = max((int(staff_id) for staff_id in staff_part_map.keys())) if len(staff_part_map.keys()) > 0 else 0 # get the current largest staff id
            staff_ids = tuple(str(staff_id + current_max_staff_id) for staff_id in staff_ids) # adjust staff ids to total scale, not just within each part (essentially, convert MuseScore 1's lack of staff ids within parts to MuseScore>1)

        # assign each staff id to a part
        for staff_id in staff_ids:
            staff_part_map[staff_id] = part_id

    # return a value or raise an error
    if not parts_info: # Raise an error if there is no Part information
        raise MuseScoreError("Part information is missing (i.e. there are no parts).")
    else:
        return parts_info, staff_part_map


def get_musescore_version(path: Union[str, Path], compressed: bool = None) -> str:
    """Determine the version of a MuseScore file.

    Parameters
    ----------
    path : str or Path
        Path to the MuseScore file to read.
    compressed : bool, optional
        Whether it is a compressed MuseScore file. Defaults to infer from the filename.

    Returns
    -------
    :str:
        Version of MuseScore
    """

    # get element tree root
    root = _get_root(path = path, compressed = compressed)

    # detect MuseScore version
    musescore_version = root.get("version")

    return musescore_version


def _get_text(element: Element, path: str, default: T = None, remove_newlines: bool = False) -> Union[str, T]:
    """Return the text of the first matching element."""
    elem = element.find(path = path)
    if elem is not None and elem.text is not None:
        if remove_newlines:
            return " ".join(elem.text.splitlines())
        return elem.text
    return default  # type: ignore


def parse_metronome(elem: Element) -> Optional[float]:
    """Return a qpm value parsed from a metronome element."""
    beat_unit = _get_text(element = elem, path = "beat-unit")
    if beat_unit is not None:
        per_minute = _get_text(element = elem, path = "per-minute")
        if per_minute is not None and beat_unit in NOTE_TYPE_MAP:
            qpm = NOTE_TYPE_MAP[beat_unit] * float(per_minute)
            if elem.find(path = "beat-unit-dot") is not None:
                qpm *= 1.5
            return qpm
    return None


def parse_time(elem: Element) -> Tuple[int, int]:
    """Return the numerator and denominator of a time element."""
    # Numerator
    beats = _get_text(element = elem, path = "sigN")
    if beats is None:
        beats = _get_text(element = elem, path = "nom1")
    if beats is None:
        raise MuseScoreError("Neither 'sigN' nor 'nom1' element is found for a TimeSig element.")
    if "+" in beats:
        numerator = sum(int(beat) for beat in beats.split("+"))
    else:
        numerator = int(beats)

    # Denominator
    beat_type = _get_text(element = elem, path = "sigD")
    if beat_type is None:
        beat_type = _get_text(element = elem, path = "den")
    if beat_type is None:
        raise MuseScoreError("Neither 'sigD' nor 'den' element is found for a TimeSig element.")
    if "+" in beat_type:
        raise RuntimeError("Compound time signatures with separate fractions are not supported.")
    denominator = int(beat_type)

    return numerator, denominator


def parse_key(elem: Element) -> Tuple[int, str, int, str]:
    """Return the key parsed from a key element."""

    mode = _get_text(element = elem, path = "mode")
    fifths_text = _get_text(element = elem, path = "accidental")  # MuseScore 2.x and 3.x
    if fifths_text is None:
        fifths_text = _get_text(element = elem, path = "subtype")  # MuseScore 1.x
        if fifths_text is None:
            fifths_text = _get_text(element = elem, path = "concertKey") # last
    if fifths_text is None:
        return None, None, None, None
        # raise MuseScoreError("'accidental', 'subtype', or 'concertKey' subelement not found for KeySig element.")
    fifths = int(fifths_text)
    if mode is None:
        return None, None, fifths, None
    idx = MODE_CENTERS[mode] + fifths
    if idx < 0 or idx > 20:
        return None, mode, fifths, None  # type: ignore
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + fifths]
    return root, mode, fifths, root_str


def parse_lyric(elem: Element) -> str:
    """Return the lyric text parsed from a lyric element."""
    text = _get_required_text(element = elem, path = "text")
    syllabic = elem.find(path = "syllabic")
    if syllabic is not None:
        if syllabic.text == "begin":
            text = f"{text} -"
        elif syllabic.text == "middle":
            text = f"- {text} -"
        elif syllabic.text == "end":
            text = f"- {text}"
    return text


def get_spanner_duration(spanner: Element, measure_len: int) -> int:
    """Returns the duration (in universal time) of a spanner element."""

    # get the duration (in measures) of the spanner
    spanner_duration = _get_text(element = spanner, path = "next/location/measures") # the duration of the spanner
    if spanner_duration is None: # if next/location/measures is not found
        return 0
    spanner_duration = float(spanner_duration) # convert to float
    fractions = _get_text(element = spanner, path = "next/location/fractions")
    if fractions is not None:
        spanner_duration += float(Fraction(fractions))

    # convert spanner to int
    # spanner_duration = round(measure_len * spanner_duration) if spanner_duration > 0 else measure_len
    spanner_duration = round(measure_len * spanner_duration)
    return spanner_duration


def parse_constant_features(
        staff: Element,
        resolution: int,
        measure_indicies: List[int],
        timeout: int = None
    ) -> Tuple[List[Tempo], List[KeySignature], List[TimeSignature], List[Barline], List[Beat], List[Annotation]]:
    """Return data parsed from a meta staff element.

    This function only parses the tempos, key and time signatures. Use `parse_staff` to parse the notes and lyrics.

    """

    # initialize lists
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    barlines: List[Barline] = []
    annotations: List[Annotation] = []

    # Initialize variables
    time_ = 0
    measure_len = round(resolution * 4)
    measure_len_fraction = 1.0
    is_tuple = False
    notes_left_in_tuple = 0
    downbeat_times: List[int] = []

    # record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # Iterate over all elements
    measures = staff.findall(path = "Measure")
    measure_indicies_improved = get_improved_measure_ordering(measures = measures, measure_indicies = measure_indicies)
    for measure_idx, measure_idx_to_actually_read in zip(measure_indicies, measure_indicies_improved):

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"Abort the process as it runned over {timeout} seconds.")

        # Get the measure element
        measure = measures[measure_idx_to_actually_read]
        is_measure_written_out = (measure_idx == measure_idx_to_actually_read)

        # Barlines, check for special types
        barline_subtype = _get_text(element = measure, path = "voice/BarLine/subtype")
        barline = Barline(time = time_, subtype = barline_subtype)
        barlines.append(barline)

        # Collect the measure start times
        downbeat_times.append(time_)

        # Get measure duration, but we don't want to recalculate every measure
        measure_len_text = measure.get("len")
        if measure_len_text is not None:
            measure_len_fraction = float(Fraction(measure_len_text))

        # get voice elements
        voices = list(measure.findall(path = "voice"))  # MuseScore 3.x, 4.x
        if not voices:
            voices = [measure]  # MuseScore 1.x and 2.x

        # Initialize position
        # max_position = float("-inf")

        # Iterate over voice elements
        for voice in voices:

            # Reset position
            position = 0

            # Iterate over child elements
            for elem in voice:

                # Key signatures
                if is_measure_written_out and elem.tag == "KeySig":
                    root, mode, fifths, root_str = parse_key(elem = elem)
                    if fifths is not None:
                        key_signatures.append(KeySignature(time = time_ + position, root = root, mode = mode, fifths = fifths, root_str = root_str))

                # Time signatures
                elif is_measure_written_out and elem.tag == "TimeSig":
                    numerator, denominator = parse_time(elem = elem)
                    measure_len = round((resolution / (denominator / 4)) * numerator)
                    time_signatures.append(TimeSignature(time = time_ + position, numerator = numerator, denominator = denominator))
                    del numerator, denominator

                # Tempo elements
                elif is_measure_written_out and elem.tag == "Tempo":
                    tempo_qpm = 60 * float(_get_required_text(element = elem, path = "tempo"))
                    tempo_text = _get_raw_text(element = elem)
                    tempos.append(Tempo(time = time_ + position, qpm = tempo_qpm, text = tempo_text))

                # Tempo spanner elements
                elif is_measure_written_out and elem.tag == "Spanner" and elem.get("type") == "GradualTempoChange" and elem.find(path = "next/location/measures") is not None:
                    tempo_spanner_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if tempo_spanner_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = TempoSpanner(duration = tempo_spanner_duration, subtype = _get_raw_text(element = elem, path = "GradualTempoChange/tempoChangeType"))))
                    del tempo_spanner_duration

                # Text spanner elements (system)
                elif is_measure_written_out and elem.tag == "Spanner" and elem.get("type") == "TextLine" and elem.find(path = "next/location/measures") is not None:
                    text_line_is_system = "system" in elem.find(path = "TextLine").attrib.keys()
                    if text_line_is_system: # only append the text spanner if it is system text
                        text_spanner_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                        if text_spanner_duration > 0:
                            annotations.append(Annotation(time = time_ + position, annotation = TextSpanner(duration = text_spanner_duration, text = _get_required_text(element = elem, path = "TextLine/beginText"), is_system = text_line_is_system)))
                        del text_spanner_duration
                # System Text
                elif is_measure_written_out and elem.tag == "SystemText": # save staff text for other function
                    annotations.append(Annotation(time = time_ + position, annotation = Text(text = _get_raw_text(element = elem, path = "text"), is_system = True, style = _get_raw_text(element = elem, path = "style"))))

                # Rehearsal Mark
                elif is_measure_written_out and elem.tag == "RehearsalMark":
                    annotations.append(Annotation(time = time_ + position, annotation = RehearsalMark(text = _get_raw_text(element = elem))))

                # Fermatas
                elif elem.tag == "Fermata":
                    annotations.append(Annotation(time = time_ + position, annotation = Fermata(is_fermata_above = (_get_text(element = elem, path = "subtype") == "fermataAbove"))))

                # Location elements
                elif elem.tag == "location":
                    duration = resolution * 4 * float(Fraction(_get_required_text(element = elem, path = "fractions")))
                    position += duration

                # Tuplet elements
                elif elem.tag == "Tuplet":
                    is_tuple = True
                    normal_notes = int(_get_required_text(element = elem, path = "normalNotes"))
                    actual_notes = int(_get_required_text(element = elem, path = "actualNotes"))
                    tuple_ratio = normal_notes / actual_notes
                    notes_left_in_tuple = actual_notes

                # Handle last tuplet note
                elif elem.tag == "endTuplet" or (is_tuple and notes_left_in_tuple == 0):
                    old_duration = round(NOTE_TYPE_MAP[duration_type] * resolution)
                    new_duration = normal_notes * old_duration - (actual_notes - 1) * round(old_duration * tuple_ratio)
                    if duration != new_duration:
                        position += int(new_duration - duration)
                    is_tuple = False

                # Rest elements
                elif elem.tag == "Rest":

                    # move time position forward if it is a rest
                    duration_type = _get_required_text(element = elem, path = "durationType")
                    if duration_type == "measure":
                        duration_text = _get_text(element = elem, path = "duration")
                        if duration_text is not None:
                            duration = (resolution * 4 * float(Fraction(duration_text)))
                        else:
                            duration = measure_len
                        position += round(duration)

                    # get duration, taking into account dots and tuples
                    else:
                        duration = NOTE_TYPE_MAP[duration_type] * resolution
                        dots = elem.find(path = "dots")
                        if dots is not None and dots.text:
                            duration *= 2 - 0.5 ** int(dots.text)
                        if is_tuple:
                            duration *= tuple_ratio
                        position += round(duration)

                # Chord elements
                elif elem.tag == "Chord":

                    # Compute duration
                    duration_type = _get_required_text(element = elem, path = "durationType")
                    duration = NOTE_TYPE_MAP[duration_type] * resolution

                    # Handle tuplets
                    if is_tuple:
                        duration *= tuple_ratio
                        notes_left_in_tuple -= 1

                    # Handle dots
                    dots = elem.find(path = "dots")
                    if dots is not None and dots.text:
                        duration *= 2 - 0.5 ** int(dots.text)

                    # Round the duration
                    duration = round(duration)

                    # Grace notes
                    is_grace = False
                    for child in elem:
                        if "grace" in child.tag or child.tag in ("appoggiatura", "acciaccatura"):
                            is_grace = True

                    # update position
                    if not is_grace:
                        position += duration

                # update positions
                # if position > max_position:
                #     max_position = position

        # update time
        # time_ += max_position # get the maximum position (don't want some unfinished voice)
        time_ += round(measure_len_fraction * measure_len)

    # Sort tempos, key and time signatures
    tempos.sort(key = attrgetter("time"))
    key_signatures.sort(key = attrgetter("time"))
    time_signatures.sort(key = attrgetter("time"))
    annotations.sort(key = attrgetter("time"))

    # Get the beats
    beats = get_beats(downbeat_times = downbeat_times, time_signatures = time_signatures, resolution = resolution, is_sorted = True)

    return tempos, key_signatures, time_signatures, barlines, beats, annotations


def parse_staff(
        staff: Element,
        resolution: int,
        measure_indicies: List[int],
        timeout: int = None,
        part_info: OrderedDict = OrderedDict([("transposeChromatic", 0)])
    ) -> Tuple[List[Note], List[Chord], List[Lyric], List[Annotation]]:
    """Return notes and lyrics parsed from a staff element.

    This function only parses the notes and lyrics. Use
    `parse_constant_features` to parse the tempos, key and time
    signatures.

    """

    # Initialize lists
    notes: List[Note] = []
    chords: List[Chord] = []
    lyrics: List[Lyric] = []
    annotations: List[Annotation] = []

    # Initialize variables
    time_ = 0
    velocity = 64
    measure_len = round(resolution * 4)
    measure_len_fraction = 1.0
    is_tuple = False
    notes_left_in_tuple = 0
    ottava_shift = 0
    ottava_end = float("inf")
    transpose_circle_of_fifths = TRANSPOSE_CHROMATIC_TO_CIRCLE_OF_FIFTHS_STEPS[part_info["transposeChromatic"] % -12] # number of semitones to transpose so that chord symbols are concert pitch

    # Record start time to check for timeout
    if timeout is not None:
        start_time = time.time()

    # Create a dictionary to handle ties
    ties: Dict[int, int] = {}

    # Iterate over all elements
    measures = staff.findall(path = "Measure")
    measure_indicies_improved = get_improved_measure_ordering(measures = measures, measure_indicies = measure_indicies)
    for measure_idx, measure_idx_to_actually_read in zip(measure_indicies, measure_indicies_improved):

        # Check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"Abort the process as it runned over {timeout} seconds.")

        # Get the measure element
        measure = measures[measure_idx_to_actually_read]
        is_measure_written_out = (measure_idx == measure_idx_to_actually_read)

        # Get measure duration, but we don't want to recalculate every measure
        measure_len_text = measure.get("len")
        if measure_len_text is not None:
            measure_len_fraction = float(Fraction(measure_len_text))

        # Get voice elements
        voices = list(measure.findall(path = "voice")) # MuseScore 3.x
        if not voices:
            voices = [measure] # MuseScore 1.x and 2.x

        # Initialize position
        # max_position = float("-inf")

        # Iterate over voice elements
        for voice in voices:

            # Initialize position
            position = 0

            # Iterate over child elements
            for elem in voice:

                # check to see if we reset ottava shift
                if (ottava_shift != 0) and ((time_ + position) >= ottava_end):
                    ottava_shift = 0

                # Dynamic elements
                if elem.tag == "Dynamic":
                    velocity = int(round(float(_get_text(element = elem, path = "velocity", default = velocity))))
                    annotations.append(Annotation(time = time_ + position, annotation = Dynamic(subtype = _get_required_text(element = elem, path = "subtype"), velocity = velocity)))

                # Hairpin elements
                elif elem.tag == "Spanner" and elem.get("type") == "HairPin" and elem.find(path = "next/location/measures") is not None:
                    hairpin_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if hairpin_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = HairPinSpanner(duration = hairpin_duration, subtype = _get_text(element = elem, path = "HairPin/beginText"), hairpin_type = int(_get_required_text(element = elem, path = "HairPin/subtype")))))
                    del hairpin_duration

                # Text spanner elements (staff)
                elif elem.tag == "Spanner" and elem.get("type") == "TextLine" and elem.find(path = "next/location/measures") is not None:
                    text_line_is_system = "system" in elem.find(path = "TextLine").attrib.keys()
                    if not text_line_is_system: # only append the text spanner if it is staff text
                        text_spanner_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                        if text_spanner_duration > 0:
                            annotations.append(Annotation(time = time_ + position, annotation = TextSpanner(duration = text_spanner_duration, text = _get_raw_text(element = elem, path = "TextLine/beginText"), is_system = text_line_is_system)))
                        del text_spanner_duration

                # Staff Text
                elif elem.tag == "StaffText":
                    annotations.append(Annotation(time = time_ + position, annotation = Text(text = _get_raw_text(element = elem), is_system = False, style = _get_raw_text(element = elem, path = "style"))))

                # Pedals
                elif elem.tag == "Spanner" and elem.get("type") == "Pedal" and elem.find(path = "next/location/measures") is not None:
                    pedal_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if pedal_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = PedalSpanner(duration = pedal_duration)))
                    del pedal_duration

                # Trill Spanners
                elif elem.tag == "Spanner" and elem.get("type") == "Trill" and elem.find(path = "next/location/measures") is not None:
                    trill_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if trill_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = TrillSpanner(duration = trill_duration, subtype = _get_text(element = elem, path = "Trill/subtype"), ornament = _get_text(element = elem, path = "Trill/Ornament/subtype"))))
                    del trill_duration

                # Vibrato Spanners
                elif elem.tag == "Spanner" and elem.get("type") == "Vibrato" and elem.find(path = "next/location/measures") is not None:
                    vibrato_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if vibrato_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = VibratoSpanner(duration = vibrato_duration, subtype = _get_text(element = elem, path = "Vibrato/subtype"))))
                    del vibrato_duration

                # Glissando Spanners
                elif elem.tag == "Spanner" and elem.get("type") == "Glissando" and elem.find(path = "next/location/measures") is not None:
                    glissando_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    if glissando_duration > 0:
                        annotations.append(Annotation(time = time_ + position, annotation = GlissandoSpanner(duration = glissando_duration, is_wavy = bool(_get_text(element = elem, path = "Trill/subtype")))))
                    del glissando_duration

                # Ottava Spanners
                elif elem.tag == "Spanner" and elem.get("type") == "Ottava" and elem.find(path = "next/location/measures") is not None:
                    ottava_time = time_ + position
                    ottava_duration = get_spanner_duration(spanner = elem, measure_len = measure_len)
                    ottava_end = ottava_time + ottava_duration
                    ottava_subtype = _get_text(element = elem, path = "Ottava/subtype")
                    ottava_shift = 12 * OTTAVA_OCTAVE_SHIFT_FACTORS[int(sub(pattern = "[^0-9]", repl = "", string = ottava_subtype))] * (-1 if "b" in ottava_subtype else 1)
                    if ottava_duration > 0:
                        annotations.append(Annotation(time = ottava_time, annotation = OttavaSpanner(duration = ottava_duration, subtype = ottava_subtype)))
                    del ottava_time, ottava_duration, ottava_subtype

                # Technical Annotation
                elif elem.tag == "PlayTechAnnotation":
                    annotations.append(Annotation(time = time_ + position, annotation = TechAnnotation(text = _get_raw_text(element = elem), tech_type = _get_raw_text(element = elem, path = "playTechType"), is_system = False)))

                # Tremolo Bar
                elif elem.tag == "TremoloBar":
                    annotations.append(Annotation(time = time_ + position, annotation = TremoloBar(points = [Point(time = int(point.get("time")), pitch = int(point.get("pitch")), vibrato = int(point.get("vibrato"))) for point in elem.findall("point")])))

                # Chord Symbol
                elif elem.tag == "Harmony":
                    root = _get_text(element = elem, path = "root")
                    if root is not None:
                        root_str = TONAL_PITCH_CLASSES[int(root) + transpose_circle_of_fifths]
                        name = _get_text(element = elem, path = "name")
                        name = name if name is not None else "Maj"
                        annotations.append(Annotation(time = time_ + position, annotation = ChordSymbol(root_str = root_str, name = name)))
                        del root_str, name
                    del root

                # Time signatures to keep track of for incrementing position
                elif is_measure_written_out and elem.tag == "TimeSig":
                    numerator, denominator = parse_time(elem = elem)
                    measure_len = round((resolution / (denominator / 4)) * numerator)
                    del numerator, denominator

                # Location elements
                elif elem.tag == "location":
                    duration = resolution * 4 * float(Fraction(_get_required_text(element = elem, path = "fractions")))
                    position += duration

                # Tuplet elements
                elif elem.tag == "Tuplet":
                    is_tuple = True
                    normal_notes = int(_get_required_text(element = elem, path = "normalNotes"))
                    actual_notes = int(_get_required_text(element = elem, path = "actualNotes"))
                    tuple_ratio = normal_notes / actual_notes
                    notes_left_in_tuple = actual_notes

                # Handle last tuplet note
                elif elem.tag == "endTuplet" or (is_tuple and notes_left_in_tuple == 0):
                    old_duration = round(NOTE_TYPE_MAP[duration_type] * resolution)
                    new_duration = normal_notes * old_duration - (actual_notes - 1) * round(old_duration * tuple_ratio)
                    if notes[-1].duration != new_duration:
                        notes[-1].duration = new_duration
                        position += int(new_duration - duration)
                    is_tuple = False

                # Rest elements
                elif elem.tag == "Rest":

                    # move time position forward if it is a rest
                    duration_type = _get_required_text(element = elem, path = "durationType")
                    if duration_type == "measure":
                        duration_text = _get_text(element = elem, path = "duration")
                        if duration_text is not None:
                            duration = (resolution * 4 * float(Fraction(duration_text)))
                        else:
                            duration = measure_len
                        position += round(duration)

                    # get duration, taking into account dots and tuples
                    else:
                        duration = NOTE_TYPE_MAP[duration_type] * resolution
                        dots = elem.find(path = "dots")
                        if dots is not None and dots.text:
                            duration *= 2 - 0.5 ** int(dots.text)
                        if is_tuple:
                            duration *= tuple_ratio
                        position += round(duration)

                # Chord elements
                elif elem.tag == "Chord":

                    # Compute duration
                    duration_type = _get_required_text(element = elem, path = "durationType")
                    duration = NOTE_TYPE_MAP[duration_type] * resolution

                    # store notations on the chord
                    chord_notations = []

                    # Handle tuplets
                    if is_tuple:
                        duration *= tuple_ratio
                        notes_left_in_tuple -= 1

                    # Handle dots
                    dots = elem.find(path = "dots")
                    if dots is not None and dots.text:
                        duration *= 2 - 0.5 ** int(dots.text)

                    # Round the duration
                    duration = round(duration)

                    # Grace notes
                    is_grace = False
                    for child in elem:
                        if "grace" in child.tag or child.tag in ("appoggiatura", "acciaccatura"):
                            is_grace = True

                    # check for slurs and ties
                    is_outgoing_tie = False
                    for spanner in elem.findall(path = "Spanner"):
                        # Check if it is a tied chord
                        if spanner.get("type") == "Tie" and ((spanner.find(path = "next/location/measures") is not None) or (spanner.find(path = "next/location/fractions") is not None)):
                            is_outgoing_tie = True

                        # Check for any slurs
                        elif spanner.get("type") == "Slur" and spanner.find(path = "next/location/measures") is not None:
                            slur_duration = get_spanner_duration(spanner = spanner, measure_len = measure_len)
                            if slur_duration > 0:
                                annotations.append(Annotation(time = time_ + position, annotation = SlurSpanner(duration = slur_duration, is_slur = True)))
                            del slur_duration

                    # Check for ornament
                    if elem.find(path = "Ornament") is not None:
                        chord_notations.append(Ornament(subtype = _get_text(element = elem, path = "Ornament/subtype")))

                    # Check for arpeggio
                    if elem.find(path = "Arpeggio") is not None:
                        arpeggio_subtype = int(_get_text(element = elem, path = "Arpeggio/subtype"))
                        arpeggio_subtype = ARPEGGIO_SUBTYPES[arpeggio_subtype if (arpeggio_subtype > 0 and arpeggio_subtype < len(ARPEGGIO_SUBTYPES)) else 0] # convert to stsring
                        annotations.append(Annotation(time = time_ + position, annotation = Arpeggio(subtype = arpeggio_subtype)))

                    # Check for tremolo
                    if elem.find(path = "Tremolo") is not None:
                        annotations.append(Annotation(time = time_ + position, annotation = Tremolo(subtype = _get_text(element = elem, path = "Tremolo/subtype"))))

                    # Check for articulation
                    if elem.find(path = "Articulation") is not None:
                        for articulation_subtype in elem.findall(path = "Articulation/subtype"): # in the case of multiple articulations
                            chord_notations.append(Articulation(subtype = articulation_subtype.text))

                    # Lyrics
                    for lyric in elem.findall(path = "Lyrics"):
                        lyric_text = parse_lyric(elem = lyric)
                        lyrics.append(Lyric(time = time_ + position, lyric = lyric_text))

                    # Collect notes
                    # chord = Chord(time = time_ + position, pitches = [], duration = duration, velocity = velocity, pitches_str = [], is_grace = is_grace)
                    for note in elem.findall(path = "Note"):

                        # notations on this specific note
                        note_notations = deepcopy(chord_notations)

                        # Get pitch
                        pitch = int(_get_required_text(element = note, path = "pitch")) + ottava_shift
                        pitch_str = TONAL_PITCH_CLASSES[int(_get_required_text(element = note, path = "tpc"))]

                        # Check for bend
                        if note.find(path = "Bend") is not None:
                            note_notations.append(Bend(points = [Point(time = int(point.get("time")), pitch = int(point.get("pitch")), vibrato = int(point.get("vibrato"))) for point in note.findall("Bend/point")]))

                        # Check for ChordLines (falls, doits, scoops, etc.)
                        if note.find(path = "ChordLine") is not None:
                            subtype = int(_get_required_text(element = note, path = "ChordLine/subtype"))
                            subtype = CHORDLINE_SUBTYPES[subtype if subtype in range(len(CHORDLINE_SUBTYPES)) else 0]
                            note_notations.append(ChordLine(subtype = subtype, is_straight = bool(_get_text(element = note, path = "ChordLine/straight"))))
                            del subtype

                        # get notehead
                        if note.find(path = "head") is not None:
                            note_notations.append(Notehead(subtype = _get_required_text(element = note, path = "head")))

                        # get symbol(s)
                        if note.find(path = "Symbol/name") is not None:
                            for symbol_name in note.findall(path = "Symbol/name"): # in the case of multiple articulations
                                note_notations.append(Symbol(subtype = symbol_name.text))

                        # Handle grace note
                        if is_grace:
                            notes.append(Note(time = time_ + position, pitch = pitch, duration = duration, velocity = velocity, pitch_str = pitch_str, is_grace = True, notations = note_notations if len(note_notations) > 0 else None))
                            # chord.pitches.append(pitch)
                            # chord.pitches_str.append(pitch_str)
                            continue

                        # Check if it is a tied note
                        for spanner in note.findall(path = "Spanner"): # MuseScore 3.x
                            if spanner.get("type") == "Tie" and ((spanner.find(path = "next/location/measures") is not None) or (spanner.find(path = "next/location/fractions") is not None)):
                                is_outgoing_tie = True
                        if note.find(path = "Tie") is not None: # MuseScore 1.x and 2.x
                            is_outgoing_tie = True

                        # Check if it is an incoming tied note
                        if pitch in ties.keys():
                            note_idx = ties[pitch]
                            notes[note_idx].duration += duration
                            if is_outgoing_tie: # if the tie continues
                                ties[pitch] = note_idx
                            else: # if the tie ended
                                del ties[pitch]

                        # Append a new note to the note list
                        else:
                            notes.append(Note(time = time_ + position, pitch = pitch, duration = duration, velocity = velocity, pitch_str = pitch_str, is_grace = False, notations = note_notations if len(note_notations) > 0 else None))
                            # chord.pitches.append(pitch)
                            # chord.pitches_str.append(pitch_str)
                            if is_outgoing_tie: # start of a tie, make note of it
                                ties[pitch] = len(notes) - 1

                    # update position
                    if not is_grace: # is a normal note that time acts on normally
                        position += duration

                    # add chord if there is stuff to add
                    # if len(chord.pitches) > 0:
                    #     chords.append(chord)
                    # del chord

                # update positions
                # if position > max_position:
                #     max_position = position

        # update time
        # time_ += max_position # get the maximum position (don't want some unfinished voice)
        time_ += round(measure_len_fraction * measure_len)

    # Sort notes
    notes.sort(key = attrgetter("time", "pitch", "duration", "velocity"))

    # Sort chords
    chords.sort(key = attrgetter("time", "duration", "velocity"))

    # Sort lyrics
    lyrics.sort(key = attrgetter("time"))

    # Sort annotations
    annotations.sort(key = attrgetter("time"))

    return notes, chords, lyrics, annotations


def read_musescore(path: Union[str, Path], resolution: int = None, compressed: bool = None, timeout: int = None) -> Music:
    """Read the MuseScore file into a Music object, paying close attention to details such as articulation and expressive features.

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
    :class:`Music`
        Converted Music object.

    """

    # get element tree for MuseScore file
    path = str(path)
    root = _get_root(path = path, compressed = compressed)
    # ET.ElementTree(root).write(f"{dirname(path)}/mscx.xml")

    # detect MuseScore version
    musescore_version = int(float(root.get("version"))) # the file format differs slightly between musescore 1 and the rest
    if musescore_version < 3:
        warnings.warn(
            f"Detected a legacy MuseScore version of {musescore_version}. "
            "Data might not be loaded correctly.",
            MuseScoreWarning,
        )

    # get the score element
    if musescore_version >= 2:
        score = root.find(path = "Score")
    else: # MuseScore 1
        score = root # No "Score" tree

    # metadata
    metadata = parse_metadata(root = root)
    metadata.source_filename = basename(path)

    # find the resolution
    if resolution is None:
        divisions = _get_divisions(root = score)
        resolution = max(divisions, key = divisions.count) if len(divisions) > 0 else muspy.DEFAULT_RESOLUTION

    # staff/part information
    parts = score.findall(path = "Part") # get all the parts
    parts_info, staff_part_map = get_part_staff_info(elem = parts, musescore_version = musescore_version)

    # get all the staff elements
    staffs = score.findall(path = "Staff")
    if len(staffs) == 0: # Return empty music object with metadata if no staff is found
        return Music(metadata = metadata, resolution = resolution)

    # parse measure ordering from the meta staff, expanding all repeats and jumps
    measure_indicies = get_measure_ordering(elem = staffs[0], timeout = timeout) # feed in the first staff, since measure ordering are constant across all staffs

    # parse the  part element
    (tempos, key_signatures, time_signatures, barlines, beats, annotations) = parse_constant_features(staff = staffs[0], resolution = resolution, measure_indicies = measure_indicies, timeout = timeout) # feed in the first staff to extract features constant across all parts

    # initialize lists
    tracks: List[Track] = []

    # record start time to check for timeout
    start_time = time.time()

    # iterate over all staffs
    part_track_map: Dict[int, int] = {} # keeps track of parts we have already looked at
    for staff in staffs:

        # check for timeout
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError(f"Abort the process as it runned over {timeout} seconds.")

        # get the staff ID
        staff_id = staff.get("id")
        if staff_id is None:
            if len(score.findall(path = "Staff")) > 1:
                continue
            staff_id = next(iter(staff_part_map))
        if staff_id not in staff_part_map:
            continue

        # parse the staff, extend/append to lists
        part_id = staff_part_map[staff_id]
        (notes, chords, lyrics, annotations_staff) = parse_staff(staff = staff, resolution = resolution, measure_indicies = measure_indicies, timeout = timeout, part_info = parts_info[part_id])
        if part_id in part_track_map:
            track_id = part_track_map[part_id]
            tracks[track_id].notes.extend(notes)
            tracks[track_id].chords.extend(chords)
            tracks[track_id].lyrics.extend(lyrics)
            tracks[track_id].annotations.extend(annotations_staff)
        else:
            part_track_map[part_id] = len(tracks)
            tracks.append(Track(program = parts_info[part_id]["program"], is_drum = parts_info[part_id]["is_drum"], name = parts_info[part_id]["name"], notes = notes, chords = chords, lyrics = lyrics, annotations = annotations_staff))

    # make sure everything is sorted
    tempos.sort(key = attrgetter("time"))
    key_signatures.sort(key = attrgetter("time"))
    time_signatures.sort(key = attrgetter("time"))
    annotations.sort(key = attrgetter("time"))
    for track in tracks:
        track.notes.sort(key = attrgetter("time", "pitch", "duration", "velocity"))
        track.chords.sort(key = attrgetter("time", "duration", "velocity"))
        track.lyrics.sort(key = attrgetter("time"))
        track.annotations.sort(key = attrgetter("time"))

    return Music(metadata = metadata, resolution = resolution, tempos = tempos, key_signatures = key_signatures, time_signatures = time_signatures, barlines = barlines, beats = beats, tracks = tracks, annotations = annotations)
