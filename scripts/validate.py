"""Validate generated SVGs and README resources without rendering libraries."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import base64
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'


def validate_svg(path):
    root = ET.parse(path).getroot()
    if root.tag != SVG+'svg':
        raise ValueError(f'{path}: not an SVG document')
    ids = [e.get('id') for e in root.iter() if e.get('id')]
    if len(ids)!=len(set(ids)):
        raise ValueError(f'{path}: duplicate SVG IDs')
    for element in root.iter():
        if element.tag in {SVG+'script',SVG+'foreignObject',SVG+'text'}:
            raise ValueError(f'{path}: unsupported or externally dependent element {element.tag}')
        for key,value in element.attrib.items():
            if key.endswith('href'):
                if element.tag==SVG+'image' and value.startswith('data:image/png;base64,'):
                    data=base64.b64decode(value.split(',',1)[1],validate=True)
                    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValueError(f'{path}: invalid inline logo PNG')
                    continue
                if not value.startswith('#') or value[1:] not in ids:
                    raise ValueError(f'{path}: unresolved or external href {value}')
            for reference in re.findall(r'url\(#([^)]*)\)',value):
                if reference not in ids:
                    raise ValueError(f'{path}: unresolved definition {reference}')
        if element.get('data-cells') is not None:
            if float(element.get('data-col'))+int(element.get('data-cells'))>int(element.get('data-cols')):
                raise ValueError(f'{path}: off-grid row')
    style=root.find(SVG+'style')
    if style is None or 'prefers-reduced-motion' not in style.text:
        raise ValueError(f'{path}: missing reduced-motion fallback')
    if path.stat().st_size>400_000:
        raise ValueError(f'{path}: SVG exceeds the 400 KB budget')


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths=[]

    def handle_starttag(self, tag, attrs):
        if tag in ('img','source'):
            values=dict(attrs)
            self.paths.append(values.get('src',values.get('srcset','')))


def validate(root=ROOT):
    paths=sorted((root/'profile').glob('*.svg'))
    expected={f'{scene}{width}-{theme}.svg' for scene in ('session','fastfetch','toolbox')
              for width in ('','-compact') for theme in ('dark','light')}
    expected.update(f'session{width}-still-{theme}.svg' for width in ('','-compact') for theme in ('dark','light'))
    if {p.name for p in paths}!=expected:
        raise ValueError('Expected 12 scene SVGs and four reduced-motion home variants')
    for path in paths:
        validate_svg(path)
    choices=sorted((root/'previews/toolbox').glob('*.svg'))
    expected={f'{style}{width}-{theme}.svg' for style in ('tree','badges','panels') for width in ('','-compact') for theme in ('dark','light')}
    if {p.name for p in choices}!=expected:
        raise ValueError('Missing or unexpected toolbox comparison assets')
    for path in choices:
        validate_svg(path)
    if not (root/'previews/toolbox-variants.html').is_file():
        raise ValueError('Missing toolbox comparison page')
    resources=Resources()
    resources.feed((root/'README.md').read_text(encoding='utf-8'))
    if len(resources.paths)!=16:
        raise ValueError('README does not reference the complete scene variants')
    for target in resources.paths:
        if '://' in target or not (root/target).is_file():
            raise ValueError(f'README resource does not resolve locally: {target}')
    print(f'Validated {len(paths)} profile SVGs + {len(choices)} toolbox choices: XML, refs, bounds, motion, size budget; 16 README paths.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    validate(args.root)


if __name__=='__main__':
    main()
