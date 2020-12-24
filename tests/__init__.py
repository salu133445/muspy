# Workaround for problem in m21ToXml caused by re-importing ElementTree
import xml.etree.ElementTree as ET
from music21.musicxml import m21ToXml
m21ToXml.ET = ET
