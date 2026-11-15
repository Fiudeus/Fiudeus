import json
from pathlib import Path
import tomllib
import tempfile
import contextlib
import io
import unittest
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

try:
    from scripts.scenes import build_scenes
except ImportError:
    build_scenes = None

ROOT = Path(__file__).resolve().parents[1]


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'config.toml').open('rb') as source:
            cls.config = tomllib.load(source)
        cls.stats = {'login': 'Fiudeus', 'fetched_at': '2026-11-14T00:00:00Z', 'repos': 10,
                     'stars': 1, 'followers': 1, 'languages': [], 'days': None,
                     'source': 'test-fixture', 'calendar_source': 'unavailable: test'}

    def test_all_palettes_and_widths_produce_self_contained_xml(self):
        self.assertIsNotNone(build_scenes, 'Scene builders must exist')
        for compact in (False, True):
            for theme in ('dark', 'light'):
                with self.subTest(compact=compact, theme=theme):
                    scenes = build_scenes(self.config, self.stats, compact, theme)
                    self.assertEqual(set(scenes), {'session','fastfetch','toolbox'})
                    for canvas in scenes.values():
                        xml = canvas.render()
                        root = ET.fromstring(xml)
                        self.assertEqual(int(root.get('width')), 540 if compact else 900)
                        self.assertNotIn('<text', xml)
                        self.assertNotIn('<foreignObject', xml)
                        ids = {e.get('id') for e in root.iter() if e.get('id')}
                        for element in root.iter():
                            if element.get('href'):
                                if element.tag=='{http://www.w3.org/2000/svg}image':
                                    self.assertTrue(element.get('href').startswith('data:image/png;base64,'))
                                    continue
                                self.assertTrue(element.get('href').startswith('#'))
                                self.assertIn(element.get('href')[1:], ids)

    def test_unavailable_metrics_never_look_like_zero(self):
        self.assertIsNotNone(build_scenes, 'Scene builders must exist')
        canvas = build_scenes(self.config, self.stats)['fastfetch']
        text = '\n'.join(item[2] for item in canvas.transcript)
        self.assertIn('n/a', text.lower())
        self.assertNotIn('0 commits', text)

    def test_last_public_activity_uses_event_time_instead_of_build_time(self):
        from scripts.generate import transcript
        stats={**self.stats,'last_public_activity':'2026-11-12T18:07:30Z'}
        for compact in (False,True):
            text=transcript(build_scenes(self.config,stats,compact)['session'])
            self.assertIn('Last public activity: 2026-11-12 18:07 UTC',text)
            self.assertNotIn('2026-11-14',text)
        unknown=transcript(build_scenes(self.config,self.stats)['session'])
        self.assertIn('Last public activity: unavailable',unknown)
        self.assertNotIn('Last login',unknown)

    def test_language_percentages_use_all_bytes_and_label_the_public_scope(self):
        from scripts.generate import transcript
        stats={**self.stats,'languages':[
            {'name':'Python','bytes':232846},
            {'name':'Jupyter Notebook','bytes':5616},
            {'name':'Shell','bytes':1377},
            {'name':'Dockerfile','bytes':644},
            {'name':'C++','bytes':581},
        ],'language_repositories':[{}]*6}
        for compact in (False,True):
            text=transcript(build_scenes(self.config,stats,compact)['fastfetch'])
            for label in ('Python 96.6%','Jupyter Notebook 2.3%','Shell 0.6%','other 0.5%','6 public repos / bytes'):
                self.assertIn(label,text)

    def test_long_configured_content_fails_usefully(self):
        self.assertIsNotNone(build_scenes, 'Scene builders must exist')
        config = {**self.config, 'profile': {**self.config['profile'], 'hello': 'a'*200}}
        with self.assertRaisesRegex(ValueError, 'row'):
            build_scenes(config, self.stats)

    def test_uptime_counts_calendar_anniversaries_across_leap_years(self):
        from scripts.scenes import uptime
        self.assertEqual(uptime('2022-04-08T00:00:00Z','2026-11-14T00:00:00Z'), '4 years, 220 days')
        self.assertEqual(uptime('2024-02-29T00:00:00Z','2028-02-29T00:00:00Z'), '4 years, 0 days')

    def test_banner_uses_configured_figlet_font_and_works_in_compact_view(self):
        from scripts.art import banner
        rows = banner('FIUDEUS', 'ansi_shadow')
        self.assertEqual(len(rows), 6)
        self.assertTrue(any('╔' in row for row in rows))
        self.assertLessEqual(max(map(len,rows)),54)

    def test_fastfetch_does_not_overwrite_the_other_column(self):
        config = {**self.config, 'profile': {**self.config['profile'], 'campus': 'C'*40}}
        with self.assertRaisesRegex(ValueError, 'fastfetch.*campus'):
            build_scenes(config, self.stats)

    def test_text_export_does_not_merge_window_chrome_into_output(self):
        from scripts.generate import transcript
        text = transcript(build_scenes(self.config, self.stats)['fastfetch'])
        self.assertEqual(text.splitlines()[0], 'Fiudeus@github ~ $ fastfetch --logo none')

    def test_toolbox_preserves_the_complete_user_requested_stack(self):
        expected = [
            ['Languages','Python / Java / C++ / SQL / Bash'],
            ['Data Analysis','NumPy / Pandas / SciPy / Matplotlib / Seaborn / Plotly'],
            ['Machine Learning','Scikit-learn / CatBoost / XGBoost'],
            ['Databases','PostgreSQL / ClickHouse / SQLite'],
            ['Development','FastAPI / SQLAlchemy / PySide6 / pytest'],
            ['Tools & Environment','Git / Docker / Linux'],
            ['Familiar with','Kotlin / HTML / CSS'],
        ]
        self.assertEqual(self.config['toolbox']['categories'],expected)
        for compact in (False,True):
            canvas = build_scenes(self.config,self.stats,compact)['toolbox']
            output = '\n'.join(item[2] for item in canvas.transcript)
            for name,technologies in expected:
                self.assertIn(name,output)
                for technology in technologies.split(' / '):
                    self.assertIn(technology,output)

    def test_toolbox_variants_preserve_all_categories_and_technology_names(self):
        for style in ('tree','badges','panels'):
            config={**self.config,'toolbox':{**self.config['toolbox'],'style':style}}
            for compact in (False,True):
                canvas=build_scenes(config,self.stats,compact)['toolbox']
                text='\n'.join(item[2] for item in canvas.transcript)
                for category,value in config['toolbox']['categories']:
                    self.assertIn(category,text)
                    for technology in value.split(' / '):
                        self.assertIn(technology,text)

    def test_generation_writes_all_toolbox_comparison_assets(self):
        from scripts.generate import generate
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                generate(self.config,self.stats,out)
            self.assertEqual(len(list((out/'previews/toolbox').glob('*.svg'))),12)
            self.assertTrue((out/'previews/toolbox-variants.html').is_file())
            from scripts.validate import validate
            with contextlib.redirect_stdout(io.StringIO()):
                validate(out)

    def test_plain_text_export_retains_names_without_private_font_symbols(self):
        from scripts.generate import transcript
        text=transcript(build_scenes(self.config,self.stats)['toolbox'])
        self.assertNotRegex(text,'[\ue000-\uf8ff\U000f0000-\U000ffffd]')
        self.assertIn('Scikit-learn',text)
        self.assertIn('Mathematics',text)

    def test_generated_readme_links_contacts_and_separates_the_three_scenes(self):
        from scripts.generate import generate

        class Readme(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links, self.images = [], []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a':
                    self.links.append(attrs['href'])
                if tag == 'img':
                    self.images.append(attrs['src'])

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                generate(self.config, self.stats, out)
            readme = Readme()
            readme.feed((out/'README.md').read_text(encoding='utf-8'))
            self.assertEqual(readme.links, [
                'https://t.me/fiudeus',
                'https://discord.com/users/735903901622206575',
                'https://vk.ru/businessqoose',
            ])
            self.assertEqual(readme.images, [
                'profile/session-light.svg',
                'profile/contact-telegram-light.svg',
                'profile/contact-discord-light.svg',
                'profile/contact-vk-light.svg',
                'profile/fastfetch-light.svg',
                'profile/ansi-palette-light.svg',
                'profile/toolbox-light.svg',
            ])
            for service in ('telegram', 'discord', 'vk'):
                for theme in ('dark', 'light'):
                    svg = ET.parse(out/'profile'/f'contact-{service}-{theme}.svg').getroot()
                    self.assertNotIn('735903901622206575', ET.tostring(svg, encoding='unicode'))

    def test_bad_contact_url_fails_before_replacing_generated_files(self):
        from scripts.generate import generate
        import copy
        config = copy.deepcopy(self.config)
        config.setdefault('contacts', {}).setdefault('telegram', {})['url'] = 'javascript:alert(1)'
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out/'README.md').write_text('previous profile', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'contact.*https'):
                generate(config, self.stats, out)
            self.assertEqual((out/'README.md').read_text(encoding='utf-8'), 'previous profile')
            self.assertFalse((out/'profile').exists())

    def test_bad_preview_input_does_not_replace_completed_outputs(self):
        from scripts.generate import generate
        import copy
        config = copy.deepcopy(self.config)
        config['contacts']['telegram']['username'] = 123456
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out/'README.md').write_text('previous profile', encoding='utf-8')
            with self.assertRaises(TypeError):
                generate(config, self.stats, out)
            self.assertEqual((out/'README.md').read_text(encoding='utf-8'), 'previous profile')
            self.assertFalse((out/'profile').exists())


if __name__ == '__main__':
    unittest.main()
