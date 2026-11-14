"""Local logo assets extracted from the user's original badges, never stand-ins."""
import base64
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import struct
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]/'assets/icons'
SVG='http://www.w3.org/2000/svg'
ET.register_namespace('',SVG)


@lru_cache(maxsize=1)
def manifest():
    return json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def registry():
    return {item['char']:item for item in manifest().values() if item['char']}


@lru_cache(maxsize=256)
def definition(ch, ink='#ffffff', paper='#000000'):
    """Keep the original marks, with terminal ink instead of brand colors.

    Vector geometry is untouched. Matplotlib's white plotting surface becomes
    the cell background, so its polar grid does not collapse into a solid disc.
    The original Seaborn PNG is a luminance mask: dark features take the cell's
    foreground and white areas become transparent. Its source bytes stay intact.
    """
    if not all(re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in (ink,paper)):
        raise ValueError('Logo ink and paper must be six-digit hex colors')
    item=registry()[ch]
    raw=(ROOT/item['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError(f'Logo checksum mismatch: {item["file"]}')
    key=f'brand-{ink[1:]}-{paper[1:]}-{ord(ch):x}'
    if item['format']=='png':
        if raw[:8]!=b'\x89PNG\r\n\x1a\n':
            raise ValueError('Invalid embedded logo PNG')
        w,h=struct.unpack('>II',raw[16:24])
        uri='data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
        filter_id=key+'-ink'
        # Inverted luminance supplies detail; SourceAlpha keeps the transparent
        # exterior transparent. Explicit ink also works in SVG <img> contexts.
        tint=(f'<filter id="{filter_id}" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">'
              '<feColorMatrix in="SourceGraphic" type="matrix" result="luminance" '
              'values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -0.2126 -0.7152 -0.0722 0 1"/>'
              '<feComposite in="luminance" in2="SourceAlpha" operator="in" result="mask"/>'
              f'<feFlood flood-color="{ink}" result="ink"/>'
              '<feComposite in="ink" in2="mask" operator="in"/></filter>')
        return key,(tint+f'<symbol id="{key}" viewBox="0 0 {w} {h}">'
                    f'<image width="{w}" height="{h}" href="{uri}" filter="url(#{filter_id})"/></symbol>')
    source=ET.fromstring(raw)
    allowed={'svg','g','path','polygon','polyline','rect','circle','ellipse','line','defs','clipPath','use','title','desc','style','linearGradient','radialGradient','stop'}
    ids={node.get('id'):key+'-'+node.get('id') for node in source.iter() if node.get('id')}
    for node in source.iter():
        if node.tag.split('}')[-1] not in allowed:
            raise ValueError('Unsupported element in local logo asset')
        for name,value in list(node.attrib.items()):
            if name.startswith('on'):
                raise ValueError('Executable logo attributes are not allowed')
            if name.endswith('href') and not value.startswith('#'):
                raise ValueError('External logo dependencies are not allowed')
            if name=='id':
                node.set(name,ids[value])
                continue
            for original,replacement in ids.items():
                value=value.replace('#'+original,'#'+replacement)
            if name in ('fill','stroke') and value.lower() not in ('none','currentcolor') and not value.startswith('url('):
                plotting_surface=(item['file']=='matplotlib.svg' and name=='fill'
                                  and value.lower() in ('#fff','#ffffff','white'))
                value=paper if plotting_surface else 'currentColor'
            node.set(name,value)
    symbol=ET.Element('{'+SVG+'}symbol',{'id':key,'viewBox':source.get('viewBox','0 0 24 24')})
    for name in ('fill','fill-rule','stroke','stroke-width','style'):
        if name in source.attrib:
            symbol.set(name,source.get(name))
    symbol.extend(list(source))
    return key,ET.tostring(symbol,encoding='unicode')
