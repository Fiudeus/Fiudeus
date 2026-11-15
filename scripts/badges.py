"""Small local contact badges and terminal samples of the profile's own colors."""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from .svg import Canvas
from .terminal import Grid, Span, cells

CONTACTS = ('telegram', 'discord', 'vk')
ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'contacts'
SVG = '{http://www.w3.org/2000/svg}'


def contact_url(config, service):
    url = config['contacts'][service]['url']
    parts = urlsplit(url)
    if (parts.scheme != 'https' or not parts.hostname or parts.username is not None
            or parts.password is not None or re.search(r'\s', url)):
        raise ValueError(f'contact {service} must have an absolute https URL')
    return url


def badge_width(config, service):
    return math.ceil(54 + cells(config['contacts'][service]['label']) * 7.8)


@lru_cache(maxsize=3)
def mark(service):
    item = json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))[service]
    raw = (ASSETS/item['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError(f'Contact logo checksum mismatch: {service}')
    source = ET.fromstring(raw)
    # The vendored Simple Icons sources contain only their original paths/title.
    if any(node.tag not in (SVG+'svg', SVG+'title', SVG+'path') for node in source.iter()):
        raise ValueError(f'Unsupported contact logo: {service}')
    paths = ''.join(f'<path d="{node.get("d")}"/>' for node in source.findall(SVG+'path'))
    return f'<symbol id="service-mark" viewBox="{source.get("viewBox")}">{paths}</symbol>'


def contact_badge(config, service, theme):
    item, colors = config['contacts'][service], config['themes'][theme]
    width = badge_width(config, service)
    canvas = Canvas(width, 28, item['label'],
                    f'{item["label"]}: {item["username"]}', colors, static=True)
    canvas.add(f'<rect width="{width}" height="28" rx="7" fill="{colors["badge_lavender"]}"/>')
    canvas.add('<path d="M7 0H34V28H7a7 7 0 0 1-7-7V7a7 7 0 0 1 7-7Z" '
               f'fill="{colors[item["accent"]]}"/>')
    canvas.define('service-mark', mark(service))
    canvas.add(f'<use href="#service-mark" x="9" y="6" width="16" height="16" fill="{colors["base"]}"/>')
    # A 24px text line centers the actual cap/x-height on the 28px badge.
    Grid(canvas, cells(item['label']), 1, 44, 0, size=13, line_height=24).line(
        0, Span(item['label'], 'text', True))
    return canvas


def ansi_palette(config, theme):
    colors = config['themes'][theme]
    ramp = colors['banner']
    if len(ramp) != 8 or any(not re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in ramp):
        raise ValueError(f'{theme} banner palette must contain exactly eight six-digit hex colors')
    canvas = Canvas(250, 28, 'Fiudeus terminal palette',
                    'Eight lavender, pink and red ANSI colors used in the FIUDEUS banner.',
                    colors, static=True)
    grid = Grid(canvas, 31, 1, 4.1, 6, size=13, line_height=16)
    grid.line(0, *(Span('███' + (' ' if index < 7 else ''), color)
                   for index, color in enumerate(ramp)))
    return canvas
