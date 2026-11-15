import unittest
from xml.etree import ElementTree as ET
import base64

from scripts.terminal import Grid,Span
from scripts.svg import Canvas
from scripts.toolbox import icon


class OriginalBadgeIconTests(unittest.TestCase):
    def test_no_invented_xgboost_icon(self):
        self.assertEqual(icon('XGBoost'),'  ')

    def test_scipy_uses_its_source_svg_instead_of_a_function_symbol(self):
        canvas=Canvas(200,50,'icons','logos',{'text':'#ffffff'})
        Grid(canvas,cols=20,rows=1,x=10,y=10).write(0,0,Span(icon('SciPy')))
        root=ET.fromstring(canvas.render())
        self.assertTrue(root.findall('.//{http://www.w3.org/2000/svg}symbol'))

    def test_seaborn_embeds_the_original_badge_image_without_network(self):
        canvas=Canvas(200,50,'icons','logos',{'text':'#ffffff'})
        Grid(canvas,cols=20,rows=1,x=10,y=10).write(0,0,Span(icon('Seaborn')))
        root=ET.fromstring(canvas.render())
        images=root.findall('.//{http://www.w3.org/2000/svg}image')
        self.assertEqual(len(images),1)
        uri=images[0].get('href')
        self.assertTrue(uri.startswith('data:image/png;base64,'))
        self.assertEqual(base64.b64decode(uri.split(',',1)[1])[:8],b'\x89PNG\r\n\x1a\n')
