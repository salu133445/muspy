"""MusicXML input interface."""
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from functools import reduce
from operator import attrgetter
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Tuple, TypeVar, Union
from xml.etree.ElementTree import Element
from zipfile import ZipFile

import numpy as np

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
from ..music import DEFAULT_RESOLUTION, Music
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
        raise MusicXMLError(
            f"Element `{path}` is required for an '{element.tag}' element."
        )
    return elem


def _get_required_attr(element: Element, attr: str) -> str:
    """Return a required attribute; raise MusicXMLError if not found."""
    attribute = element.get(attr)
    if attribute is None:
        raise MusicXMLError(
            f"Attribute '{attr}' is required for an '{element.tag}' element."
        )
    return attribute


def _get_required_text(
    element: Element, path: str, remove_newlines: bool = False
) -> str:
    """Return a required text; raise MusicXMLError if not found."""
    elem = _get_required(element, path)
    if elem.text is None:
        raise MusicXMLError(
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


def parse_key_elem(elem: Element) -> Tuple[int, str, int, str]:
    """Return the key parsed from a key element."""
    mode = _get_text(elem, "mode")
    fifths = int(_get_required_text(elem, "fifths"))
    if mode is None:
        return None, None, fifths, None
    idx = MODE_CENTERS[mode] + fifths
    if idx < 0 or idx > 20:
        return None, mode, fifths, None  # type: ignore
    root, root_str = CIRCLE_OF_FIFTHS[MODE_CENTERS[mode] + fifths]
    return root, mode, fifths, root_str


def parse_time_elem(elem: Element) -> Tuple[int, int]:
    """Return the numerator and denominator of a time element."""
    # Numerator
    beats = _get_required_text(elem, "beats")
    if "+" in beats:
        numerator = sum(int(beat) for beat in beats.split("+"))
    else:
        numerator = int(beats)

    # Denominator
    beat_type = _get_required_text(elem, "beat-type")
    if "+" in beat_type:
        raise RuntimeError(
            "Compound time signatures with separate fractions "
            "are not supported."
        )
    denominator = int(beat_type)

    return numerator, denominator


def parse_pitch_elem(elem: Element) -> Tuple[int, str]:
    """Return the pitch and pitch_str of a pitch element."""
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


def parse_unpitched_elem(elem: Element) -> Tuple[int, str]:
    """Return the pitch and pitch_str of an unpitched element."""
    step = _get_required_text(elem, "display-step")
    octave = int(_get_required_text(elem, "display-octave"))
    pitch = 12 * (octave + 1) + NOTE_MAP[step]
    pitch_str = step + str(octave)
    return pitch, pitch_str


def parse_lyric_elem(elem: Element) -> Optional[str]:
    """Return the lyric text parsed from a lyric element."""
    text = _get_text(elem, "text")
    if text is None:
        return None
    syllabic_elem = elem.find("syllabic")
    if syllabic_elem is not None:
        if syllabic_elem.text == "begin":
            text = f"{text} -"
        elif syllabic_elem.text == "middle":
            text = f"- {text} -"
        elif syllabic_elem.text == "end":
            text = f"- {text}"
    return text


def get_measure_ordering(elem: Element) -> List[int]:
    """Return a list of measure indices parsed from a part element.

    This function returns the ordering of measures, considering all
    repeats and jumps.

    """
    # Measure indices
    measure_indices = []

    # Repeats
    is_after_repeat = False
    last_repeat = 0
    count_repeat: DefaultDict[int, int] = defaultdict(lambda: 1)
    count_ending = 1
    is_repeat_done: DefaultDict[int, bool] = defaultdict(lambda: False)

    # Coda, tocoda, dacapo, segno, dalsegno, fine
    is_after_jump = False
    is_dacapo = False
    is_fine = False
    is_dalsegno = False
    is_segno = False
    is_after_segno = False
    is_tocoda = False
    is_coda = False
    is_after_coda = False
    is_jump_done: DefaultDict[int, bool] = defaultdict(lambda: False)

    # Iterate over all elements
    measure_idx = 0
    measure_elems = list(elem.findall("measure"))
    while measure_idx < len(measure_elems):

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Handle segno
        if is_dalsegno and not is_after_segno:
            # Look for segno
            for sound_elem in measure_elem.findall("sound"):
                if sound_elem.get("segno") is not None:
                    is_segno = True
            for sound_elem in measure_elem.findall("direction/sound"):
                if sound_elem.get("segno") is not None:
                    is_segno = True

            # Skip if it is not segno
            if not is_segno:
                measure_idx += 1
                continue

            is_after_segno = True

        # Handle coda
        if is_tocoda and not is_after_coda:
            # Look for coda
            for sound_elem in measure_elem.findall("sound"):
                if sound_elem.get("coda") is not None:
                    is_coda = True
            for sound_elem in measure_elem.findall("direction/sound"):
                if sound_elem.get("coda") is not None:
                    is_coda = True

            # Skip if it is not coda
            if not is_coda:
                measure_idx += 1
                continue

            is_after_coda = True

        # Set the default next measure
        next_measure_idx = measure_idx + 1

        # Sound element
        for sound_elem in measure_elem.findall("sound"):
            if is_after_jump:
                # Tocoda
                if sound_elem.get("tocoda") is not None:
                    is_tocoda = True

                # Fine
                if sound_elem.get("fine") is not None:
                    is_fine = True
            elif not is_jump_done[measure_idx]:
                # Dacapo
                if sound_elem.get("dacapo") is not None:
                    is_dacapo = True
                    next_measure_idx = 0

                # Daselgno
                if sound_elem.get("dalsegno") is not None:
                    is_dalsegno = True
                    next_measure_idx = 0

        # Sound elements under direction elements
        for sound_elem in measure_elem.findall("direction/sound"):
            if is_after_jump:
                # Tocoda
                if sound_elem.get("tocoda") is not None:
                    is_tocoda = True

                # Fine
                if sound_elem.get("fine") is not None:
                    is_fine = True
            elif not is_jump_done[measure_idx]:
                # Dacapo
                if sound_elem.get("dacapo") is not None:
                    is_dacapo = True
                    next_measure_idx = 0

                # Daselgno
                if sound_elem.get("dalsegno") is not None:
                    is_dalsegno = True
                    next_measure_idx = 0

        # Break the loop if it is fine
        if is_after_jump and is_fine:
            measure_indices.append(measure_idx)
            break

        # Ending elements
        ending_elem = measure_elem.find("barline/ending")
        if ending_elem is not None:
            ending_num_attr = _get_required_attr(ending_elem, "number")
            ending_num = [int(num) for num in ending_num_attr.split(",")]
            # Skip the current measure if not the correct ending
            if count_ending not in ending_num:
                measure_idx += 1
                # Reset the flag
                is_after_repeat = False
                continue

        # Repeat elements
        repeat_elem = measure_elem.find("barline/repeat")
        if repeat_elem is not None:
            direction = _get_required_attr(repeat_elem, "direction")
            if direction == "forward":
                last_repeat = measure_idx
                # Reset repeat counters
                if not is_after_repeat:
                    count_repeat[measure_idx] = 1
                    count_ending = 1
            elif direction == "backward":
                # Get after-jump infomation
                after_jump_attr = repeat_elem.get("after-jump")
                if after_jump_attr is None or after_jump_attr == "no":
                    after_jump = False
                else:
                    after_jump = True
                if not is_after_jump or (is_after_jump and after_jump):
                    # Get repeat-times infomation
                    repeat_times_attr = repeat_elem.get("times")
                    if repeat_times_attr is None:
                        repeat_times = 2
                    else:
                        repeat_times = int(repeat_times_attr)
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
                        is_after_repeat = False
                        is_repeat_done[measure_idx] = True
                        count_repeat[measure_idx] = 1
                        count_ending = 1
            else:
                raise MusicXMLError(
                    "Unknown direction for a `repeat` element : "
                    f"{direction}"
                )

        # Append the current measure index to the list to be return
        measure_indices.append(measure_idx)

        if not is_after_jump and (is_dacapo or is_dalsegno):
            is_after_jump = True
            is_jump_done[measure_idx] = True

        measure_idx = next_measure_idx

    return measure_indices


def get_beats(
    downbeat_times: List[int],
    time_signatures: List[TimeSignature],
    resolution: int = DEFAULT_RESOLUTION,
    is_sorted: bool = False,
) -> List[Beat]:
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
    list of :class:`muspy.Beat`
        Computed beats.

    """
    # Return a list of downbeats if no time signatures is given
    if not time_signatures:
        return [Beat(time=int(round(time))) for time in downbeat_times]

    # Sort the downbeats and time signatures if necessary
    if not is_sorted:
        downbeat_times = sorted(downbeat_times)
        time_signatures = sorted(time_signatures, key=attrgetter("time"))

    # Compute the beats
    beats: List[Beat] = []
    sign_idx = 0
    downbeat_idx = 0
    while downbeat_idx < len(downbeat_times):
        # Select the correct time signatures
        if (
            sign_idx + 1 < len(time_signatures)
            and downbeat_times[downbeat_idx]
            < time_signatures[sign_idx + 1].time
        ):
            sign_idx += 1
            continue

        # Set time signature
        time_sign = time_signatures[sign_idx]
        beat_resolution = resolution / (time_sign.denominator / 4)

        # Get the next downbeat
        if downbeat_idx < len(downbeat_times) - 1:
            end: float = downbeat_times[downbeat_idx + 1]
        else:
            end = (
                downbeat_times[downbeat_idx]
                + beat_resolution * time_sign.numerator
            )

        # Append beats
        start = int(round(downbeat_times[downbeat_idx]))
        beat_times = np.arange(start, end, beat_resolution)
        for time in beat_times:
            beats.append(Beat(time=int(round(time))))

        downbeat_idx += 1

    return beats


def parse_meta_part_elem(
    part_elem: Element, resolution: int, measure_indices: List[int]
) -> Tuple[
    List[Tempo],
    List[KeySignature],
    List[TimeSignature],
    List[Barline],
    List[Beat],
]:
    """Return data parsed from a meta part element.

    This function only parses the tempos, key and time signatures. Use
    `parse_part_elem` to parse the notes and lyrics.

    """
    # Initialize lists
    tempos: List[Tempo] = []
    key_signatures: List[KeySignature] = []
    time_signatures: List[TimeSignature] = []
    barlines: List[Barline] = []

    # Initialize variables
    time = 0
    division = 1
    downbeat_times: List[int] = []

    # Iterate over all elements
    measure_elems = list(part_elem.findall("measure"))
    for measure_idx in measure_indices:

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Barlines
        barlines.append(Barline(time=time))

        # Collect the measure start times
        downbeat_times.append(time)

        # Initialize position
        position = 0
        last_note_position = None

        # Iterating over all elements in the current measure
        for elem in measure_elem:

            # Attributes elements
            if elem.tag == "attributes":
                # Division elements
                division_elem = elem.find("divisions")
                if (
                    division_elem is not None
                    and division_elem.text is not None
                ):
                    division = int(division_elem.text)

                # Key elements
                key_elem = elem.find("key")
                if key_elem is not None:
                    root, mode, fifths, root_str = parse_key_elem(key_elem)
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
                time_elem = elem.find("time")
                if time_elem is not None:
                    numerator, denominator = parse_time_elem(time_elem)
                    time_signatures.append(
                        TimeSignature(
                            time=time + position,
                            numerator=numerator,
                            denominator=denominator,
                        )
                    )

            # Sound element
            elif elem.tag == "sound":
                # Tempo elements
                tempo = elem.get("tempo")
                if tempo is not None:
                    tempos.append(Tempo(time + position, float(tempo)))

            # Direction elements
            elif elem.tag == "direction":
                # TODO: Handle textual tempo markings
                tempo_set = False

                # Sound elements
                sound_elem_ = elem.find("sound")
                if sound_elem_ is not None:
                    # Tempo directions
                    tempo = sound_elem_.get("tempo")
                    if tempo is not None:
                        tempos.append(
                            Tempo(time=time + position, qpm=float(tempo))
                        )
                        tempo_set = True

                # Metronome elements
                if not tempo_set:
                    metronome_elem = elem.find("direction-type/metronome")
                    if metronome_elem is not None:
                        qpm = parse_metronome_elem(metronome_elem)
                        if qpm is not None:
                            tempos.append(Tempo(time=time + position, qpm=qpm))

            # Note elements
            elif elem.tag == "note":
                # TODO: Handle voice information

                # Rest elements
                rest_elem = elem.find("rest")
                if rest_elem is not None:
                    # Move time position forward if it is a rest
                    duration = int(_get_required_text(elem, "duration"))
                    position += round(duration * resolution / division)
                    continue

                # Cue notes
                if elem.find("cue") is not None:
                    continue

                # Chord elements
                if elem.find("chord") is not None:
                    # Move time position backward if it is in a chord
                    if last_note_position is not None:
                        position = last_note_position

                # Grace notes
                grace_elem = elem.find("grace")
                if grace_elem is not None:
                    continue

                # Get duration
                duration = int(_get_required_text(elem, "duration"))

                # Move time position forward if it is not in chord
                last_note_position = position
                position += round(duration * resolution / division)

            # Forward elements
            elif elem.tag == "forward":
                duration = int(_get_required_text(elem, "duration"))
                position += round(duration * resolution / division)

            # Backup elements
            elif elem.tag == "backup":
                duration = int(_get_required_text(elem, "duration"))
                position -= round(duration * resolution / division)

        time += position

    # Sort tempos, key and time signatures
    barlines.sort(key=attrgetter("time"))
    tempos.sort(key=attrgetter("time"))
    key_signatures.sort(key=attrgetter("time"))
    time_signatures.sort(key=attrgetter("time"))

    # Get the beats
    beats = get_beats(
        downbeat_times, time_signatures, resolution, is_sorted=True
    )

    return tempos, key_signatures, time_signatures, barlines, beats


def parse_part_elem(
    part_elem: Element,
    resolution: int,
    instrument_info: dict,
    measure_indices: List[int],
) -> Tuple[Dict[str, List[Note]], List[Lyric]]:
    """Return notes and lyrics parsed from a part element.

    This function only parses the notes and lyrics. Use
    `parse_meta_part_elem` to parse the tempos, key and time signatures.

    """
    # Initialize lists
    notes: Dict[str, List[Note]] = {
        instrument_id: [] for instrument_id in instrument_info
    }
    lyrics: List[Lyric] = []

    # Initialize variables
    time = 0
    velocity = 64
    division = 1
    default_instrument_id = next(iter(instrument_info))
    transpose_semitone = 0
    transpose_octave = 0

    # Create a dictionary to handle ties
    ties: Dict[Tuple[str, int], int] = {}

    # Iterate over all elements
    measure_elems = list(part_elem.findall("measure"))
    for measure_idx in measure_indices:

        # Get the measure element
        measure_elem = measure_elems[measure_idx]

        # Initialize position
        position = 0
        last_note_position = None

        # Iterating over all elements in the current measure
        for elem in measure_elem:

            # Attributes elements
            if elem.tag == "attributes":
                # Division elements
                division_elem = elem.find("divisions")
                if (
                    division_elem is not None
                    and division_elem.text is not None
                ):
                    division = int(division_elem.text)

                # Transpose elements
                transpose_elem = elem.find("transpose")
                if transpose_elem is not None:
                    transpose_semitone = int(
                        _get_required_text(transpose_elem, "chromatic")
                    )
                    octave_change = _get_text(transpose_elem, "octave-change")
                    if octave_change is not None:
                        transpose_octave = int(octave_change)

            # Sound element
            elif elem.tag == "sound":
                # Dynamics elements
                dynamics = elem.get("dynamics")
                if dynamics is not None:
                    velocity = round(float(dynamics))

            # Direction elements
            elif elem.tag == "direction":
                # TODO: Handle textual dynamic markings
                # Sound elements
                sound_elem_ = elem.find("sound")
                if sound_elem_ is not None:
                    # Dynamic directions
                    dynamics = sound_elem_.get("dynamics")
                    if dynamics is not None:
                        velocity = round(float(dynamics))

            # Note elements
            elif elem.tag == "note":
                # TODO: Handle voice information

                # Rest elements
                rest_elem = elem.find("rest")
                if rest_elem is not None:
                    # Move time position forward if it is a rest
                    duration = int(_get_required_text(elem, "duration"))
                    position += round(duration * resolution / division)
                    continue

                # Cue notes
                if elem.find("cue") is not None:
                    continue

                # Chord elements
                if elem.find("chord") is not None:
                    # Move time position backward if it is in a chord
                    if last_note_position is not None:
                        position = last_note_position

                # Get pitch number and string
                unpitched_elem = elem.find("unpitched")
                if unpitched_elem is not None:
                    # Unpitched notes
                    pitch, pitch_str = parse_unpitched_elem(unpitched_elem)
                else:
                    # Normal pitches
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

                # Grace notes
                grace_elem = elem.find("grace")
                if grace_elem is not None:
                    note_type = _get_required_text(elem, "type")
                    notes[instrument_id].append(
                        Note(
                            time=time + position,
                            pitch=pitch,
                            duration=round(
                                NOTE_TYPE_MAP[note_type] * resolution
                            ),
                            velocity=velocity,
                            pitch_str=pitch_str,
                        )
                    )
                    continue

                # Get duration
                duration = int(_get_required_text(elem, "duration"))

                # Check if it is a tied note
                # (Should we look for a tie or tied element?)
                is_outgoing_tie = False
                for tie_elem in elem.findall("tie"):
                    if tie_elem.get("type") == "start":
                        is_outgoing_tie = True

                # Check if it is an incoming tied note
                note_key = (instrument_id, pitch)
                if note_key in ties:
                    note_idx = ties[note_key]
                    notes[instrument_id][note_idx].duration += round(
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
                            duration=round(duration * resolution / division),
                            velocity=velocity,
                            pitch_str=pitch_str,
                        )
                    )

                    if is_outgoing_tie:
                        ties[note_key] = len(notes[instrument_id]) - 1

                # Lyrics
                lyric_elem = elem.find("lyric")
                if lyric_elem is not None:
                    lyric_text = parse_lyric_elem(lyric_elem)
                    if lyric_text is not None:
                        lyrics.append(
                            Lyric(time=time + position, lyric=lyric_text)
                        )

                # Move time position forward if it is not in chord
                last_note_position = position
                position += round(duration * resolution / division)

            # Forward elements
            elif elem.tag == "forward":
                duration = int(_get_required_text(elem, "duration"))
                position += round(duration * resolution / division)

            # Backup elements
            elif elem.tag == "backup":
                duration = int(_get_required_text(elem, "duration"))
                position -= round(duration * resolution / division)

        time += position

    # Sort notes
    for instrument_notes in notes.values():
        instrument_notes.sort(
            key=attrgetter("time", "pitch", "duration", "velocity")
        )

    # Sort lyrics
    lyrics.sort(key=attrgetter("time"))

    return notes, lyrics


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
    """Return the root of the element tree."""
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
    path: Union[str, Path], resolution: int = None, compressed: bool = None
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

    # Get the meta staff, assuming the first staff
    meta_part_elem = root.find("part")

    # Return empty music object with metadata if no staff is found
    if meta_part_elem is None:
        return Music(metadata=metadata, resolution=resolution)

    # Parse measure ordering from the meta part, expanding all repeats
    # and jumps
    measure_indices = get_measure_ordering(meta_part_elem)

    # Parse the meta part element
    (
        tempos,
        key_signatures,
        time_signatures,
        barlines,
        beats,
    ) = parse_meta_part_elem(meta_part_elem, resolution, measure_indices)

    # Initialize lists
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
        notes, lyrics = parse_part_elem(
            part_elem, resolution, instrument_info, measure_indices
        )
        tracks.append(
            Track(program=0, is_drum=False, notes=notes[""], lyrics=lyrics)
        )

    else:
        # Iterate over all parts and measures
        for part_elem in root.findall("part"):
            part_id = part_elem.get("id")
            if part_id is None:
                if len(root.findall("part")) > 1:
                    continue
                part_id = next(iter(part_info))
            if part_id not in part_info:
                continue

            # Parse part
            notes, lyrics = parse_part_elem(
                part_elem, resolution, part_info[part_id], measure_indices
            )

            # Extend lists
            for instrument_id, instrument_notes in notes.items():
                track = Track(
                    program=part_info[part_id][instrument_id]["program"],
                    is_drum=part_info[part_id][instrument_id]["is_drum"],
                    name=part_info[part_id][instrument_id]["name"],
                    notes=instrument_notes,
                    lyrics=lyrics,
                )
                tracks.append(track)

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
