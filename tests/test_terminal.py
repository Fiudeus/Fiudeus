import unittest
from xml.etree import ElementTree as ET

try:
    from scripts.svg import Canvas
    from scripts.terminal import Grid, Span, cells
except ImportError:
    Canvas = Grid = Span = cells = None


class TerminalTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Grid, 'The terminal grid renderer must exist')
        self.canvas = Canvas(240, 120, 'A < B', 'A terminal & its output', {'text': '#ffffff'})
        self.grid = Grid(self.canvas, cols=20, rows=4, x=10, y=10, size=15, line_height=23)

    def test_unicode_width_does_not_follow_font_advance(self):
        self.assertEqual(cells('e\u0301→█'), 3)
        self.assertEqual(cells('A界B'), 4)
        with self.assertRaises(ValueError):
            cells('hello\tworld')

    def test_combining_text_does_not_shift_next_glyph(self):
        self.grid.write(0, 0, Span('e\u0301x'))
        root = ET.fromstring(self.canvas.render())
        uses = root.findall('.//{http://www.w3.org/2000/svg}use')
        self.assertEqual(len(uses), 2)
        self.assertEqual(float(uses[1].get('x')), 19.0)

    def test_reuses_glyph_definitions_and_escapes_metadata(self):
        self.grid.write(0, 0, Span('aaa <&>'))
        root = ET.fromstring(self.canvas.render())
        defs = root.find('{http://www.w3.org/2000/svg}defs')
        ids = [e.get('id') for e in defs.iter() if e.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len([x for x in ids if x.endswith('-0061')]), 1)
        self.assertEqual(root.find('{http://www.w3.org/2000/svg}title').text, 'A < B')

    def test_overflow_is_an_error_instead_of_clipping(self):
        with self.assertRaisesRegex(ValueError, 'row 0.*20'):
            self.grid.write(19, 0, Span('long'))
        with self.assertRaisesRegex(ValueError, 'row'):
            self.grid.write(0, 4, Span('x'))

    def test_unsupported_character_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'U\\+1F680'):
            self.grid.write(0, 0, Span('🚀'))

    def test_box_drawing_and_blocks_are_grid_geometry(self):
        self.grid.write(0, 0, Span('┌─┐'))
        self.grid.write(0, 1, Span('│█│'))
        xml = self.canvas.render()
        root = ET.fromstring(xml)
        self.assertGreater(len(root.findall('.//{http://www.w3.org/2000/svg}path')), 0)
        self.assertIn('data-text="│█│"', xml)

    def test_ansi_background_stays_on_its_own_character_cells(self):
        self.grid.write(2,1,Span(' Python ','text',background='#303040'))
        root=ET.fromstring(self.canvas.render())
        rects=[r for r in root.findall('.//{http://www.w3.org/2000/svg}rect') if r.get('fill')=='#303040']
        self.assertEqual(len(rects),1)
        self.assertEqual([float(rects[0].get(k)) for k in ('x','y','width','height')],[28,33,72,23])

    def test_brand_icon_reserves_two_cells_without_shifting_the_label(self):
        self.assertEqual(cells('\ue73c'),2)
        self.grid.write(0,0,Span('\ue73c Python'))
        root=ET.fromstring(self.canvas.render())
        uses=root.findall('.//{http://www.w3.org/2000/svg}use')
        self.assertEqual(float(uses[1].get('x')),37)
        self.assertTrue(any(e.get('id','').endswith('-e73c') for e in root.iter()))


if __name__ == '__main__':
    unittest.main()
