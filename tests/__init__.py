"""Test suites."""
# Workaround for problem in m21ToXml caused by re-importing ElementTree.
# See https://github.com/salu133445/muspy/issues/18
import xml.etree.ElementTree as ET

from music21.musicxml import m21ToXml

m21ToXml.ET = ET
