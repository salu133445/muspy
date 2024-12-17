"""Utility functions."""
from collections import OrderedDict
from typing import Dict, List, Tuple
import numpy as np
import warnings

import yaml

NOTE_MAP: Dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

CIRCLE_OF_FIFTHS: List[Tuple[int, str]] = [
    (4, "Fb"),
    (11, "Cb"),
    (6, "Gb"),
    (1, "Db"),
    (8, "Ab"),
    (3, "Eb"),
    (10, "Bb"),
    (5, "F"),  # Lydian
    (0, "C"),  # Major/Ionian
    (7, "G"),  # Mixolydian
    (2, "D"),  # Dorian
    (9, "A"),  # Minor/Aeolian
    (4, "E"),  # Phrygian
    (11, "B"),  # Locrian
    (6, "F#"),
    (1, "C#"),
    (8, "G#"),
    (3, "D#"),
    (10, "A#"),
    (5, "E#"),
    (0, "B#"),
]

MODE_CENTERS = {
    "major": 8,
    "minor": 11,
    "lydian": 7,
    "ionian": 8,
    "mixolydian": 9,
    "dorian": 10,
    "aeolian": 11,
    "phrygian": 12,
    "locrian": 13,
}

NOTE_TYPE_MAP: Dict[str, float] = {
    "1024th": 0.00390625,
    "512th": 0.0078125,
    "256th": 0.015625,
    "128th": 0.03125,
    "64th": 0.0625,
    "32nd": 0.125,
    "16th": 0.25,
    "eighth": 0.5,
    "quarter": 1.0,
    "half": 2.0,
    "whole": 4.0,
    "breve": 8.0,
    "long": 16.0,
    "maxima": 32.0,
}

TONAL_PITCH_CLASSES = {
    -1: "Fbb",
    0: "Cbb",
    1: "Gbb",
    2: "Dbb",
    3: "Abb",
    4: "Ebb",
    5: "Bbb",
    6: "Fb",
    7: "Cb",
    8: "Gb",
    9: "Db",
    10: "Ab",
    11: "Eb",
    12: "Bb",
    13: "F",
    14: "C",
    15: "G",
    16: "D",
    17: "A",
    18: "E",
    19: "B",
    20: "F#",
    21: "C#",
    22: "G#",
    23: "D#",
    24: "A#",
    25: "E#",
    26: "B#",
    27: "F##",
    28: "C##",
    29: "G##",
    30: "D##",
    31: "A##",
    32: "E##",
    33: "B##",
}


def note_str_to_note_num(note_str: str):
    """Return the note number of a note string.

    The regular expression for the note string is `[A-G][#b]*`. The base
    note must be capitalized. There can be multiple accidentals, where
    '#' denotes a sharp and 'b' denotes a flat. Some examples include
    'C'->0, 'D#'->3, 'Eb'->3.

    Parameters
    ----------
    note_str : str
        Note string.

    Returns
    -------
    int, 0-11
        Note number.

    """
    note_num = NOTE_MAP.get(note_str[0])
    if note_num is None:
        raise ValueError(
            f"Expect a base note from 'A' to 'G', but got :{note_str[0]}."
        )
    for alter in note_str[1:]:
        if alter == "#":
            note_num += 1
        elif alter == "b":
            note_num -= 1
        else:
            raise ValueError(
                f"Expect an accidental of '#' or 'b', but got : {alter}."
            )
    if note_num > 11 or note_num < 0:
        return note_num % 12
    return note_num


class OrderedDumper(yaml.SafeDumper):
    """A dumper that supports OrderedDict."""


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


OrderedDumper.add_representer(OrderedDict, _dict_representer)


def yaml_dump(
    data, Dumper=None, allow_unicode: bool = True, **kwargs
):  # pylint: disable=invalid-name
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """
    if Dumper is None:
        Dumper = OrderedDumper
    return yaml.dump(
        data, Dumper=Dumper, allow_unicode=allow_unicode, **kwargs
    )

class ChordSymbolParser(object):
    # Modified version of:
    # https://github.com/DCMLab/pitchplots/blob/master/modified_musicxml_parser.py#L908
    # Renders to mir_eval compatible chords.
    # Time representation is taken from caller and transition is
    # implemented in the classes.ChordSymbol class, so state has been removed.
    """Internal representation of a MusicXML chord symbol <harmony> element.
    This represents a chord symbol with four components:
    1) Root: a string representing the chord root pitch class, e.g. "C#".
    2) Kind: a string representing the chord kind, e.g. "m7" for minor-seventh,
            "9" for dominant-ninth, or the empty string for major triad.
    3) Scale degree modifications: a list of strings representing scale degree
            modifications for the chord, e.g. "add9" to add an unaltered ninth scale
            degree (without the seventh), "b5" to flatten the fifth scale degree,
            "no3" to remove the third scale degree, etc.
    4) Bass: a string representing the chord bass pitch class, or None if the bass
            pitch class is the same as the root pitch class.
    5) Binary_xml: 12D binary representation of chord pitch classes. This is used
            to find the proper matching quality in mir_eval.chord.
    There's also a special chord kind "N.C." representing no harmony, for which
    all other fields should be None.
    Use the `get_figure_string` method to get a string representation of the chord
    symbol as might appear in a lead sheet. This string representation is what we
    use to represent chord symbols in NoteSequence protos, as text annotations.
    While the MusicXML representation has more structure, using an unstructured
    string provides more flexibility and allows us to ingest chords from other
    sources, e.g. guitar tabs on the web.
    """

    # The below dictionary maps chord kinds to an abbreviated string as would
    # appear in a chord symbol in a standard lead sheet. There are often multiple
    # standard abbreviations for the same chord type, e.g. "+" and "aug" both
    # refer to an augmented chord, and "maj7", "M7", and a Delta character all
    # refer to a major-seventh chord; this dictionary attempts to be consistent
    # but the choice of abbreviation is somewhat arbitrary.
    #
    # The MusicXML-defined chord kinds are listed here:
    # http://usermanuals.musicxml.com/MusicXML/Content/ST-MusicXML-kind-value.htm

    CHORD_KIND_ABBREVIATIONS = {
            # These chord kinds are in the MusicXML spec.
            'major': '',
            'minor': 'm',
            'augmented': 'aug',
            'augmented-major-seventh': 'aug',
            'diminished': 'dim',
            'dominant': '7',
            'major-seventh': 'maj7',
            'minor-seventh': 'm7',
            'seventh-flat-five': '7(b5)',
            'diminished-seventh': 'dim7',
            'augmented-seventh': 'aug7',
            'half-diminished': 'm7b5',
            'major-minor': 'm(maj7)',
            'major-sixth': '6',
            'minor-sixth': 'm6',
            'dominant-ninth': '9',
            'major-ninth': 'maj9',
            'minor-ninth': 'm9',
            'dominant-11th': '11',
            'major-11th': 'maj11',
            'minor-11th': 'm11',
            'dominant-13th': '13',
            'major-13th': 'maj13',
            'minor-13th': 'm13',
            'suspended-second': 'sus2',
            'suspended-fourth': 'sus',
            'suspended-fourth-seventh': 'sus',
            'pedal': 'ped',
            'power': '5',
            'none': 'N.C.',

            # These are not in the spec, but show up frequently in the wild.
            'dominant-seventh': '7',
            'augmented-ninth': 'aug9',
            'minor-major': 'm(maj7)',

            # Some abbreviated kinds also show up frequently in the wild.
            '': '',
            'min': 'm',
            'aug': 'aug',
            'dim': 'dim',
            '7': '7',
            'maj7': 'maj7',
            'min7': 'm7',
            'dim7': 'dim7',
            'm7b5': 'm7b5',
            'minMaj7': 'm(maj7)',
            '6': '6',
            'min6': 'm6',
            'maj69': '6(add9)',
            '9': '9',
            'maj9': 'maj9',
            'min9': 'm9',
            'sus47': 'sus7',

            # added from
            # https://lilypond.org/doc/v2.25/input/regression/musicxml/collated-files#g_t71-_002e_002e_002e-guitar-notation
            'Neapolitan': '',
            'Italian': '7',
            'French': '7',
            'German': '7',
            'Tristan': '9',
            'other': 'ped'
    }

    KIND_TO_BINARY = {
        '': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        'm': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
        'aug': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'dim': [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        '7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        'maj7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        'm7': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
        'dim7': [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
        'aug7': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0],
        'm7b5': [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
        'm(maj7)': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        '6': [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
        'm6': [1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
        '9': [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        'maj9': [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        'm9': [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
        '11': [1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0],
        'maj11': [1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1],
        'm11': [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0],
        '13': [1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0],
        'maj13': [1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1],
        'm13': [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0],
        'sus2': [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        'sus': [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
        'ped': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        '5': [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        'N.C.': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'aug9': [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0],
        'sus7': [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0],
        '6(add9)': [1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    }

    def __init__(self, xml_harmony, time):
        self.xml_harmony = xml_harmony
        self.root = None
        self.kind = ''
        self.degrees = []
        self.binary = np.zeros(12)
        self.bass = None
        self.time = time
        self._parse()

    def _alter_to_string(self, alter_text):
        """Parse alter text to a string of one or two sharps/flats.
        Args:
            alter_text: A string representation of an integer number of semitones.
        Returns:
            A string, one of 'bb', 'b', '#', '##', or the empty string.
        Raises:
            ChordSymbolParseError: If `alter_text` cannot be parsed to an integer,
                    or if the integer is not a valid number of semitones between -2 and 2
                    inclusive.
        """
        # Parse alter text to an integer number of semitones.
        try:
            alter_semitones = int(alter_text)
        except ValueError:
            warnings.warn('Non-integer alter: ' + str(alter_text))

        # Visual alter representation
        if alter_semitones == -2:
            alter_string = 'bb'
        elif alter_semitones == -1:
            alter_string = 'b'
        elif alter_semitones == 0:
            alter_string = ''
        elif alter_semitones == 1:
            alter_string = '#'
        elif alter_semitones == 2:
            alter_string = '##'
        else:
            warnings.warn('Invalid alter: ' + str(alter_semitones))

        return alter_string

    def _parse(self):
        """Parse the MusicXML <harmony> element."""
        for child in self.xml_harmony:
            if child.tag == 'root':
                self._parse_root(child)
            elif child.tag == 'kind':
                if child.text is None:
                    # Seems like this shouldn't happen but frequently does in the wild...
                    continue
                kind_text = str(child.text).strip()
                if kind_text not in self.CHORD_KIND_ABBREVIATIONS:
                    warnings.warn('Unknown chord kind: ' + kind_text)
                self.kind = self.CHORD_KIND_ABBREVIATIONS[kind_text]
                self.binary = np.array( self.KIND_TO_BINARY[self.kind] )
            elif child.tag == 'degree':
                tmp_degree = self._parse_degree(child)
                self.apply_degree(tmp_degree)
                self.degrees.append( tmp_degree )
            elif child.tag == 'bass':
                self._parse_bass(child)
            elif child.tag == 'offset':
                # Offset tag moves chord symbol time position.
                try:
                    offset = int(child.text)
                except ValueError:
                    warnings.warn('Non-integer offset: ' + str(child.text))
            else:
                # Ignore other tag types because they are not relevant to Magenta.
                pass

        if self.root is None and self.kind != 'N.C.':
            warnings.warn('Chord symbol must have a root')

    def apply_degree(self, d):
        if 'no' in d:
            d_num = d.split('no')[1]
            if d_num == '5':
                if self.binary[7] == 0:
                    self.binary[6] = 0
                else:
                    self.binary[7] = 0
            elif d_num == '3':
                if self.binary[4] == 0:
                    self.binary[3] = 0
                else:
                    self.binary[4] = 0
            elif d_num == '7':
                if self.binary[10] == 0:
                    self.binary[11] = 0
                else:
                    self.binary[10] = 0
        else:
            if 'add' in d:
                # just remove 'add'
                d = d.split('add')[1]
            modifier = 0
            if '#' in d:
                modifier = 1
            if 'b' in d:
                modifier = -1
            if '11' in d:
                self.binary[ 5 + modifier] = 0
            if '9' in d or '2' in d:
                self.binary[ 2 + modifier] = 0
            if '13' in d or '6' in d:
                self.binary[ 9 + modifier] = 0




    def _parse_pitch(self, xml_pitch, step_tag, alter_tag):
        """Parse and return the pitch-like <root> or <bass> element."""
        if xml_pitch.find(step_tag) is None:
            warnings.warn('Missing pitch step')
        step = xml_pitch.find(step_tag).text

        alter_string = ''
        if xml_pitch.find(alter_tag) is not None:
            alter_text = xml_pitch.find(alter_tag).text
            alter_string = self._alter_to_string(alter_text)

        return step + alter_string

    def _parse_root(self, xml_root):
        """Parse the <root> tag for a chord symbol."""
        self.root = self._parse_pitch(xml_root, step_tag='root-step', alter_tag='root-alter')

    def _parse_bass(self, xml_bass):
        """Parse the <bass> tag for a chord symbol."""
        self.bass = self._parse_pitch(xml_bass, step_tag='bass-step', alter_tag='bass-alter')

    def _parse_degree(self, xml_degree):
        """Parse and return the <degree> scale degree modification element."""
        if xml_degree.find('degree-value') is None:
            warnings.warn('Missing scale degree value in harmony')
        value_text = xml_degree.find('degree-value').text
        if value_text is None:
            warnings.warn('Missing scale degree')
        try:
            value = int(value_text)
        except ValueError:
            warnings.warn(
                    'Non-integer scale degree: ' + str(value_text))

        alter_string = ''
        if xml_degree.find('degree-alter') is not None:
            alter_text = xml_degree.find('degree-alter').text
            alter_string = self._alter_to_string(alter_text)

        if xml_degree.find('degree-type') is None:
            warnings.warn('Missing degree modification type')
        type_text = xml_degree.find('degree-type').text

        if type_text == 'add':
            if not alter_string:
                # When adding unaltered scale degree, use "add" string.
                type_string = 'add'
            else:
                # When adding altered scale degree, "add" not necessary.
                type_string = ''
        elif type_text == 'subtract':
            type_string = 'no'
            # Alter should be irrelevant when removing scale degree.
            alter_string = ''
        elif type_text == 'alter':
            if not alter_string:
                warnings.warn('Degree alteration by zero semitones')
            # No type string necessary as merely appending e.g. "#9" suffices.
            type_string = ''
        else:
            warnings.warn(
                    'Invalid degree modification type: ' + str(type_text))

        # Return a scale degree modification string that can be appended to a chord
        # symbol figure string.
        return type_string + alter_string + str(value)

    def __str__(self):
        if self.kind == 'N.C.':
            note_string = '{kind: ' + self.kind + '} '
        else:
            note_string = '{root: ' + self.root
            note_string += ', kind: ' + self.kind
            note_string += ', degrees: [%s]' % ', '.join(degree for degree in self.degrees)
            note_string += ', binary: ' + repr(self.binary)
            if self.bass:
                note_string += ', bass: ' + self.bass + '} '
        note_string += '} '
        note_string += '(@time: ' + str(self.time) + ')'
        return note_string

    def get_figure_string(self):
        """Return a chord symbol figure string."""
        if self.kind == 'N.C.':
            return self.kind
        else:
            degrees_string = ''.join('(%s)' % degree for degree in self.degrees)
            figure = self.root + self.kind + degrees_string
            if self.bass:
                figure += '/' + self.bass
            return figure
# end class ChordSymbolParser
