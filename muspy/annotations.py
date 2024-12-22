"""Annotation classes.

This module defines the annotation classes of MusPy,
which represent expression markings present in music.

Classes
-------

- Arpeggio
- Articulation
- Bend
- ChordLine
- ChordSymbol
- Dynamic
- Fermata
- GlissandoSpanner
- HairPinSpanner
- Notehead
- Ornament
- OttavaSpanner
- PedalSpanner
- Point
- RehearsalMark
- SlurSpanner
- Spanner
- Subtype
- SubtypeSpanner
- Symbol
- TechAnnotation
- TempoSpanner
- Text
- TextSpanner
- Tremolo
- TremoloBar
- TrillSpanner
- VibratoSpanner

"""
from collections import OrderedDict
from typing import Any, List

from .base import Base, ComplexBase
from .classes import DEFAULT_VELOCITY

__all__ = [
    "Arpeggio",
    "Articulation",
    "Bend",
    "ChordLine",
    "ChordSymbol",
    "Dynamic",
    "Fermata",
    "GlissandoSpanner",
    "HairPinSpanner",
    "Notehead",
    "Ornament",
    "OttavaSpanner",
    "PedalSpanner",
    "Point",
    "RehearsalMark",
    "SlurSpanner",
    "Spanner",
    "Subtype",
    "SubtypeSpanner",
    "Symbol",
    "TechAnnotation",
    "TempoSpanner",
    "Text",
    "TextSpanner",
    "Tremolo",
    "TremoloBar",
    "TrillSpanner",
    "VibratoSpanner",
]

# pylint: disable=super-init-not-called


class Text(Base):
    """A container for text.
    Meant to be stored as an annotation, so the class itself has no timestamp (the timestamp is stored in the annotation object).

    Attributes
    ----------
    text : str
        The text contained in the text element.
    is_system : bool, default: False
        Is this text system-wide (True) or just for a specific staff (False)?
    style : str, optional
        The style of the text element.

    """

    _attributes = OrderedDict([("text", str), ("is_system", bool), ("style", str)])
    _optional_attributes = ["is_system", "style"]

    def __init__(self, text: str, is_system: bool = False, style: str = None):
        self.text = "" if text is None else text
        self.is_system = bool(is_system)
        self.style = style


class Subtype(Base):
    """A container for objects with the a subtype attribute.

    Attributes
    ----------
    subtype : Any
        The subtype attribute.

    """

    _attributes = OrderedDict([("subtype", object)])

    def __init__(self, subtype):
        self.subtype = subtype


class RehearsalMark(Text):
    """A container for rehearsal marks.

    Attributes
    ----------
    text : str
        The text contained in the text element.
    is_system : bool, default: True
        Is this text system-wide (True) or just for a specific staff (False)?
    style : str, optional
        The style of the text.

    """

    _attributes = OrderedDict([("text", str), ("is_system", bool), ("style", str)])
    _optional_attributes = ["is_system", "style"]

    def __init__(self, text: str, is_system: bool = True, style: str = None):
        super().__init__(text = text, is_system = is_system, style = style)


class ChordSymbol(Text):
    """A container for chord symbols.

    Attributes
    ----------
    root_str : str
        Root pitch as a string, useful for distinguishing, e.g., C# and Db.
    name : str, default: 'Maj'
        The text contained in the chord symbol element.
    text : str, optional
        The full text contained in the chord symbol.
    is_system : bool, default: False
        Is this text system-wide (True) or just for a specific staff (False)?
    style : str, optional
        The style of the text.

    """

    _attributes = OrderedDict([("root_str", str), ("name", str), ("text", str), ("is_system", bool), ("style", str)])
    _optional_attributes = ["name", "text", "is_system", "style"]

    def __init__(self, root_str: str, name: str = "Maj", text: str = None, is_system: bool = False, style: str = None):
        super().__init__(text = root_str + (name if name else "") if text is None else text, is_system = is_system, style = style)
        self.root_str = root_str
        self.name = name


class TechAnnotation(Text):
    """A container for technical annotations.

    Attributes
    ----------
    text : str
        The text contained in the text element.
    tech_type : str, optional
        The type of technical annotation to play.
    is_system : bool, default: False
        Is this text system-wide (True) or just for a specific staff (False)?
    style : str, optional
        The style of the text.

    """

    _attributes = OrderedDict([("text", str), ("tech_type", str), ("is_system", bool), ("style", str)])
    _optional_attributes = ["tech_type", "is_system", "style"]

    def __init__(self, text: str, tech_type: str = None, is_system: bool = False, style: str = None):
        super().__init__(text = text, is_system = is_system, style = style)
        self.tech_type = tech_type


class Dynamic(Subtype):
    """A container for dynamic markings.

    Attributes
    ----------
    subtype : str
        The type of dynamic.
    velocity : int, default: `muspy.DEFAULT_VELOCITY` (64)
        The velocity associated with the dynamic marking.

    """

    _attributes = OrderedDict([("subtype", str), ("velocity", int)])
    _optional_attributes = ["velocity"]

    def __init__(self, subtype: str, velocity: int = DEFAULT_VELOCITY):
        super().__init__(subtype = subtype)
        self.velocity = velocity


class Fermata(Subtype):
    """A container for fermatas.
    Meant to be stored as an annotation, so the class itself has no timestamp (the timestamp is stored in the annotation object).

    Attributes
    ----------
    is_fermata_above : bool, default: True
        Whether this fermata is above or below the note to which it applies.
    subtype : str, optional
        The subtype of fermata contained in the text element.

    """

    _attributes = OrderedDict([("is_fermata_above", bool), ("subtype", str)])
    _optional_attributes = ["is_fermata_above", "subtype"]

    def __init__(self, is_fermata_above: bool = True, subtype: str = None):
        self.is_fermata_above = bool(is_fermata_above)
        if subtype is None:
            subtype = "fermata above" if self.is_fermata_above else "fermata below"
        super().__init__(subtype = subtype)


class Arpeggio(Subtype):
    """A container for arpeggios.

    Attributes
    ----------
    subtype : str, default: 'default'
        Arpeggio subtype.

    """

    _attributes = OrderedDict([("subtype", str)])
    _optional_attributes = ["subtype"]

    def __init__(self, subtype: str = "default"):
        super().__init__(subtype = subtype)


class Tremolo(Subtype):
    """A container for tremolos.

    Attributes
    ----------
    subtype : str, default: 'r8'
        Tremolo subtype.

    """

    _attributes = OrderedDict([("subtype", str)])
    _optional_attributes = ["subtype"]

    def __init__(self, subtype: str = "r8"):
        super().__init__(subtype = subtype)


class ChordLine(Subtype):
    """A container for MuseScore ChordLines.

    Attributes
    ----------
    subtype : str, default: 'fall'
        Subtype of the ChordLine.
    is_straight : bool, default: False
        Is the ChordLine straight?

    """

    _attributes = OrderedDict([("subtype", str), ("is_straight", bool)])
    _optional_attributes = ["subtype", "is_straight"]

    def __init__(self, subtype: str = "fall", is_straight: bool = False):
        super().__init__(subtype = subtype)
        self.is_straight = bool(is_straight)


class Ornament(Subtype):
    """A container for ornaments.

    Attributes
    ----------
    subtype : str
        Ornament subtype.

    """

    _attributes = OrderedDict([("subtype", str)])

    def __init__(self, subtype: str):
        super().__init__(subtype = subtype)


class Articulation(Subtype):
    """A container for articulations.

    Attributes
    ----------
    subtype : str
        Articulation subtype.

    """

    _attributes = OrderedDict([("subtype", str)])

    def __init__(self, subtype: str):
        super().__init__(subtype = subtype)


class Notehead(Subtype):
    """A container for noteheads.

    Attributes
    ----------
    subtype : str
        Notehead subtype.

    """

    _attributes = OrderedDict([("subtype", str)])

    def __init__(self, subtype: str):
        super().__init__(subtype = subtype)


class Symbol(Subtype):
    """A container for symbols.

    Attributes
    ----------
    subtype : str
        Symbol subtype.

    """

    _attributes = OrderedDict([("subtype", str)])

    def __init__(self, subtype: str):
        super().__init__(subtype = subtype)


class Point(Base):
    """A container for MuseScore Point objects.

    Attributes
    ----------
    time : int
        The time of the point (in time steps).
    pitch : int
        The pitch of the point.
    vibrato : int, default: 0
        The vibrato.

    """

    _attributes = OrderedDict([("time", int), ("pitch", int), ("vibrato", int)])
    _optional_attributes = ["vibrato"]

    def __init__(self, time: int, pitch: int, vibrato: int = 0):
        self.time = int(time)
        self.pitch = int(pitch)
        self.vibrato = int(vibrato)


class Bend(ComplexBase):
    """A container for bends.

    Attributes
    ----------
    points : List[:class:`muspy.Point`]
        List of points that make up the bend.

    """

    _attributes = OrderedDict([("points", Point)])
    _list_attributes = ["points"]

    def __init__(self, points: List[Point]):
        self.points = points


class TremoloBar(Bend):
    """A container for MuseScore TremoloBar objects.

    Attributes
    ----------
    points : List[:class:`muspy.Point`]
        List of points that make up the TremoloBar.

    """

    _attributes = OrderedDict([("points", Point)])
    _list_attributes = ["points"]

    def __init__(self, points: List[Point]):
        super().__init__(points = points)


class Spanner(Base):
    """A parent-class container for MuseScore Spanners.
    Meant to be stored as an annotation, so the class itself has no timestamp (the timestamp is stored in the annotation object).

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.

    """

    _attributes = OrderedDict([("duration", int)])

    def __init__(self, duration: int):
        self.duration = duration


class SubtypeSpanner(Subtype, Spanner):
    """A container for spanners whose only attribute is a subtype.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    subtype : Any
        Subtype.

    """

    _attributes = OrderedDict([("duration", int), ("subtype", object)])

    def __init__(self, duration: int, subtype: object):
        Subtype.__init__(self = self, subtype = subtype)
        Spanner.__init__(self = self, duration = duration)


class TempoSpanner(SubtypeSpanner):
    """A container for spanners relating to a tempo change.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    subtype : str
        Type of tempo change.

    """

    _attributes = OrderedDict([("duration", int), ("subtype", str)])

    def __init__(self, duration: int, subtype: str):
        super().__init__(duration = duration, subtype = subtype)


class TextSpanner(Text, Spanner):
    """A container for text that spans a specific duration.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    text : str
        The text contained in the text element.
    is_system : bool, default: False
        Is this text system-wide (True) or just for a specific staff (False)?
    style : str, optional
        The style of the text.

    """

    _attributes = OrderedDict([("duration", int), ("text", str), ("is_system", bool), ("style", str)])
    _optional_attributes = ["is_system", "style"]

    def __init__(self, duration: int, text: str, is_system: bool = False, style: str = None):
        Text.__init__(self = self, text = text, is_system = is_system, style = style)
        Spanner.__init__(self = self, duration = duration)


class HairPinSpanner(SubtypeSpanner):
    """A container for hairpins (crescendos, decrescendos).

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    subtype : str, optional
        The text associated with the hairpin spanner.
    hairpin_type : int, default: -1
        The type of hairpin found within the MusicXML element.

    """

    _attributes = OrderedDict([("duration", int), ("subtype", str), ("hairpin_type", int)])
    _optional_attributes = ["subtype", "hairpin_type"]

    def __init__(self, duration: int, subtype: str = None, hairpin_type: int = -1):
        super().__init__(duration = duration, subtype = subtype)
        self.hairpin_type = hairpin_type


class SlurSpanner(SubtypeSpanner):
    """A container for slurs.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    is_slur : bool, default: True
        Is this object a slur (True), meaning it connects different
        pitches, or a tie (False), meaning it connects the same pitch?
    subtype : str, optional
        If not provided, `subtype` is set to 'slur' or 'tie', depending
        on the `is_slur` argument.

    """

    _attributes = OrderedDict([("duration", int), ("is_slur", bool), ("subtype", str)])
    _optional_attributes = ["is_slur", "subtype"]

    def __init__(self, duration: int, is_slur: bool = True, subtype: str = None):
        self.is_slur = bool(is_slur)
        if subtype is None:
            subtype = "slur" if self.is_slur else "tie"
        super().__init__(duration = duration, subtype = subtype)


class PedalSpanner(Spanner):
    """A container for pedal markings.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.

    """

    _attributes = OrderedDict([("duration", int)])

    def __init__(self, duration: int):
        super().__init__(duration = duration)


class TrillSpanner(SubtypeSpanner):
    """A container for trill spanners.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    subtype : str, default: 'trill'
        Subtype of trill.
    ornament : str, optional
        Subtype of ornament associated with the trill.

    """

    _attributes = OrderedDict([("duration", int), ("subtype", str), ("ornament", str)])
    _optional_attributes = ["subtype", "ornament"]

    def __init__(self, duration: int, subtype: str = "trill", ornament: str = None):
        super().__init__(duration = duration, subtype = subtype)
        self.ornament = ornament


class VibratoSpanner(SubtypeSpanner):
    """A container for MuseScore Vibrato elements.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps
    subtype : str, default: 'vibratoSawtooth'
        Subtype of vibrato

    """

    _attributes = OrderedDict([("duration", int), ("subtype", str)])
    _optional_attributes = ["subtype"]

    def __init__(self, duration: int, subtype: str = "vibratoSawtooth"):
        super().__init__(duration = duration, subtype = subtype)


class GlissandoSpanner(SubtypeSpanner):
    """A container for glissando markings.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    is_wavy : bool, optional, default: False
        Is this Glissano wavy (True) or straight (False)?
    subtype : str, optional, default: 'straight'
        If not provided, `subtype` is set to 'wavy' or 'straight', depending
        on the `is_wavy` argument.

    """

    _attributes = OrderedDict([("duration", int), ("is_wavy", bool), ("subtype", str)])
    _optional_attributes = ["is_wavy", "subtype"]

    def __init__(self, duration: int, is_wavy: bool = False, subtype: str = None):
        self.is_wavy = bool(is_wavy)
        if subtype is None:
            subtype = "wavy" if self.is_wavy else "straight"
        super().__init__(duration = duration, subtype = subtype)


class OttavaSpanner(SubtypeSpanner):
    """A container for ottava markings.

    Attributes
    ----------
    duration : int
        Duration of spanner, in time steps.
    subtype : str, optional, default: '8va'
        Subtype of ottava.

    """

    _attributes = OrderedDict([("duration", int), ("subtype", str)])
    _optional_attributes = ["subtype"]

    def __init__(self, duration: int, subtype: str = "8va"):
        super().__init__(duration = duration, subtype = subtype)
