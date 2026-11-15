"""Small, escaped SVG document builder; no browser or network dependencies."""
from contextlib import contextmanager
from html import escape
import re


def number(value: float) -> str:
    return f'{value:.3f}'.rstrip('0').rstrip('.') or '0'


class Canvas:
    def __init__(self, width, height, title, description, palette, *, static=False):
        self.width, self.height = width, height
        self.title, self.description, self.palette = title, description, palette
        self.static = static
        self.defs = {}
        self.styles = {}
        self.body = []
        self.transcript = []

    def add(self, element):
        self.body.append(element)

    def define(self, key, element):
        self.defs.setdefault(key, element)

    def style(self, key, value):
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', key):
            raise ValueError(f'Invalid CSS identifier: {key!r}')
        if key in self.styles and self.styles[key] != value:
            raise ValueError(f'Conflicting animation: {key}')
        self.styles[key] = value

    @contextmanager
    def group(self, css):
        self.add(f'<g class="{escape(css, quote=True)}">')
        yield
        self.add('</g>')

    def render(self):
        title = escape(self.title)
        desc = escape(self.description)
        styles = ''.join(self.styles.values())
        styles += '@media(prefers-reduced-motion:reduce){*{animation:none!important}}'
        if self.static:
            styles += '*{animation:none!important}'
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{title}</title><desc id="desc">{desc}</desc>'
            f'<style>{escape(styles)}</style><defs>{"".join(self.defs.values())}</defs>'
            f'{"".join(self.body)}</svg>\n'
        )
