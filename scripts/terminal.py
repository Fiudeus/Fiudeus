"""Unicode-aware fixed cells, local outlined glyphs and seamless TUI symbols.

Width is a terminal property (wcwidth), never a font metric. Fonts are local,
versioned assets. The writer refuses unsupported glyphs and off-grid output.
"""
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
import unicodedata

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from wcwidth import wcwidth, wcswidth

from .svg import number
from .icons import registry,definition as icon_definition

FONT_ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'


@lru_cache(maxsize=1)
def icon_characters():
    return frozenset(registry())


def character_cells(ch):
    # Logos reserve two text cells, independent of their vector/raster source.
    return 2 if ord(ch)>=0xe000 and ch in icon_characters() else wcwidth(ch)


def cells(text: str) -> int:
    width = wcswidth(text)
    if width < 0 or any(unicodedata.category(ch) == 'Cc' for ch in text):
        raise ValueError('Control characters are not allowed inside a terminal row')
    return width+sum(1 for ch in text if ord(ch)>=0xe000 and ch in icon_characters())


@dataclass(frozen=True)
class Span:
    text: str
    color: str = 'text'
    bold: bool = False
    background: str | None = None


@lru_cache(maxsize=2)
def font(bold=False):
    name = 'JetBrainsMono-Bold.ttf' if bold else 'JetBrainsMono-Regular.ttf'
    result = TTFont(FONT_ROOT / name)
    return result, result.getBestCmap(), result.getGlyphSet()


@lru_cache(maxsize=4096)
def outline(ch, size, bold):
    tt, cmap, glyphs = font(bold)
    if ord(ch) not in cmap:
        raise ValueError(f'Unsupported glyph U+{ord(ch):04X} {ch!r}; choose a glyph in the bundled fonts')
    pen = SVGPathPen(glyphs, ntos=number)
    scale = size / tt['head'].unitsPerEm
    glyphs[cmap[ord(ch)]].draw(TransformPen(pen, (scale, 0, 0, -scale, 0, 0)))
    return pen.getCommands()


BOX = {
    '─': 'lr', '│': 'ud', '┌': 'rd', '┐': 'ld', '└': 'ru', '┘': 'lu',
    '├': 'rud', '┤': 'lud', '┬': 'lrd', '┴': 'lru', '┼': 'lrud',
    '╭': 'rd', '╮': 'ld', '╰': 'ru', '╯': 'lu',
}


class Grid:
    def __init__(self, canvas, cols, rows, x, y, size=15, line_height=23, record=True):
        self.canvas, self.cols, self.rows = canvas, cols, rows
        self.x, self.y, self.size, self.line_height = x, y, size, line_height
        self.cell_width = size * .6
        self.record = record
        if x < 0 or y < 0 or x + cols * self.cell_width > canvas.width + .01:
            raise ValueError('Terminal grid exceeds horizontal canvas bounds')
        if y + rows * line_height > canvas.height + .01:
            raise ValueError('Terminal grid exceeds vertical canvas bounds')

    def _symbol(self, ch, x, y, ink, paper):
        w, h = self.cell_width, self.line_height
        n = number
        if ch in icon_characters():
            key,source=icon_definition(ch,ink,paper)
            self.canvas.define(key,source)
            return (f'<use href="#{key}" x="{n(x+(2*w-self.size)/2)}" y="{n(y+(h-self.size)/2+2)}" '
                    f'width="{n(self.size)}" height="{n(self.size)}"/>')
        if ch in BOX:
            cx, cy = x + w / 2, y + h / 2
            points = {'l': (x, cy), 'r': (x+w, cy), 'u': (cx, y), 'd': (cx, y+h)}
            d = ''.join(f'M{n(cx)} {n(cy)}L{n(points[k][0])} {n(points[k][1])}' for k in BOX[ch])
            # A scaled subpixel stroke can disappear with crispEdges. Keep a
            # full viewport pixel when an SVG is rasterized at a reduced size.
            return f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
        if ch in '═║╔╗╚╝':
            cx, cy, gap = x+w/2, y+h/2, 1.45
            if ch == '═':
                d = f'M{n(x)} {n(cy-gap)}H{n(x+w)}M{n(x)} {n(cy+gap)}H{n(x+w)}'
            elif ch == '║':
                d = f'M{n(cx-gap)} {n(y)}V{n(y+h)}M{n(cx+gap)} {n(y)}V{n(y+h)}'
            else:
                right, down = ch in '╔╚', ch in '╔╗'
                edge_x, edge_y = x+w if right else x, y+h if down else y
                sx, sy = -1 if right else 1, -1 if down else 1
                d = ''.join(f'M{n(edge_x)} {n(cy+sign*sy*gap)}H{n(cx+sign*sx*gap)}V{n(edge_y)}' for sign in (1,-1))
            return f'<path d="{d}" fill="none" stroke="currentColor" stroke-width=".9"/>'
        if ch in '█▀▄':
            dy = h / 2 if ch == '▄' else 0
            height = h if ch == '█' else h / 2
            # Adjacent block cells share an exact device-pixel edge even when
            # GitHub scales the image to a fractional size on mobile screens.
            return f'<path d="M{n(x)} {n(y+dy)}h{n(w)}v{n(height)}h{n(-w)}Z" shape-rendering="crispEdges"/>'
        if ch in '▁▂▃▅▆▇':
            fraction = {'▁': 1, '▂': 2, '▃': 3, '▅': 5, '▆': 6, '▇': 7}[ch] / 8
            height = h * fraction
            return f'<path d="M{n(x)} {n(y+h-height)}h{n(w)}v{n(height)}h{n(-w)}Z"/>'
        if ch in '░▒▓':
            gid = f'shade-{ord(ch)}-{round(w*10)}-{round(h*10)}'
            density = '░▒▓'.index(ch) + 1
            path = []
            nx, ny = 4, 8
            for iy in range(ny):
                for ix in range(nx):
                    pattern = (ix % 2) + 2 * (iy % 2)
                    if pattern < density:
                        px, py = ix*w/nx, iy*h/ny
                        path.append(f'M{n(px)} {n(py)}h{n(w/nx)}v{n(h/ny)}h{n(-w/nx)}Z')
            self.canvas.define(gid, f'<path id="{gid}" d="{"".join(path)}"/>')
            return f'<use href="#{gid}" x="{n(x)}" y="{n(y)}"/>'
        return None

    def fragment(self, col, row, *spans):
        spans = tuple(Span(s) if isinstance(s, str) else s for s in spans)
        text = ''.join(s.text for s in spans)
        width = cells(text)
        if not isinstance(row, int) or row < 0 or row >= self.rows:
            raise ValueError(f'Invalid terminal row {row}; expected 0..{self.rows-1}')
        if col < 0 or col + width > self.cols:
            raise ValueError(f'Text on row {row} needs columns {col}..{col+width}, grid has {self.cols}: {text!r}')
        output, cursor = [], col
        for span in spans:
            color = self.canvas.palette.get(span.color, span.color)
            if not color.startswith('#'):
                raise ValueError(f'Unknown terminal color {span.color!r}')
            parts = []
            paper = self.canvas.palette.get('base','#000000')
            if span.background:
                background=self.canvas.palette.get(span.background,span.background)
                if not background.startswith('#'):
                    raise ValueError(f'Unknown terminal background {span.background!r}')
                paper=background
                parts.append(f'<rect x="{number(self.x+cursor*self.cell_width)}" y="{number(self.y+row*self.line_height)}" '
                             f'width="{number(cells(span.text)*self.cell_width)}" height="{number(self.line_height)}" fill="{background}"/>')
            for ch in unicodedata.normalize('NFC', span.text):
                width_ch = character_cells(ch)
                if ch != ' ':
                    x = self.x + (cursor if width_ch else max(col, cursor - 1)) * self.cell_width
                    y = self.y + row * self.line_height
                    symbol = self._symbol(ch, x, y, color, paper)
                    if symbol is None:
                        gid = f'g-{"b" if span.bold else "r"}-{round(self.size*10)}-{ord(ch):04x}'
                        self.canvas.define(gid, f'<path id="{gid}" d="{outline(ch, self.size, span.bold)}"/>')
                        baseline = y + (self.line_height-self.size)/2 + self.size
                        symbol = f'<use href="#{gid}" x="{number(x)}" y="{number(baseline)}"/>'
                    parts.append(symbol)
                cursor += max(0, width_ch)
            output.append(f'<g fill="{color}" color="{color}">{"".join(parts)}</g>')
        return (f'<g data-row="{row}" data-col="{col}" data-cells="{width}" '
                f'data-cols="{self.cols}" data-text="{escape(text, quote=True)}">{"".join(output)}</g>')

    def write(self, col, row, *spans, css=''):
        fragment = self.fragment(col, row, *spans)
        if css:
            fragment = f'<g class="{escape(css, quote=True)}">{fragment}</g>'
        self.canvas.add(fragment)
        if self.record:
            self.canvas.transcript.append((row, col, ''.join(s if isinstance(s, str) else s.text for s in spans)))
        return fragment

    def line(self, row, *spans, css=''):
        return self.write(0, row, *spans, css=css)
