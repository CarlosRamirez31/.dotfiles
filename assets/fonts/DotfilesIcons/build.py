"""Regenerate Dotfiles Icons from the bundled Simple Icons SVG (fonttools required)."""
from pathlib import Path
import xml.etree.ElementTree as ET
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path

root = Path(__file__).resolve().parent
builder = FontBuilder(1000, isTTF=True)
builder.setupGlyphOrder(['.notdef', 'hackthebox'])
builder.setupCharacterMap({0xE000: 'hackthebox'})
empty = TTGlyphPen(None)
pen = TTGlyphPen(None)
outline = TransformPen(Cu2QuPen(pen, 1, reverse_direction=True), (37.5, 0, 0, -37.5, 50, 800))
svg = ET.parse(root / 'hackthebox.svg').getroot()
parse_path(svg.find('{http://www.w3.org/2000/svg}path').attrib['d'], outline)
builder.setupGlyf({'.notdef': empty.glyph(), 'hackthebox': pen.glyph()})
builder.setupHorizontalMetrics({'.notdef': (1000, 0), 'hackthebox': (1000, 106)})
builder.setupHorizontalHeader(ascent=850, descent=-150)
builder.setupNameTable({'familyName': 'Dotfiles Icons', 'styleName': 'Regular',
                       'uniqueFontIdentifier': 'DotfilesIcons-Regular-1.0',
                       'fullName': 'Dotfiles Icons Regular', 'psName': 'DotfilesIcons-Regular',
                       'version': 'Version 1.0'})
builder.setupOS2(sTypoAscender=850, sTypoDescender=-150, usWinAscent=850, usWinDescent=150)
builder.setupPost()
builder.save(root / 'DotfilesIcons-Regular.ttf')
