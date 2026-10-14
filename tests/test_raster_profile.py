"""Regression fixtures test tracing behavior; they are not evidence of AI recognition."""
import tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from hgcloud.raster_profile import trace,area
from hgcloud.core import SceneError
ROOT=Path(__file__).resolve().parents[1]
class RasterProfileTests(unittest.TestCase):
    def fixture(self,drawer):
        td=tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='profile-test-');self.addCleanup(td.cleanup)
        p=Path(td.name)/'drawing.png';im=Image.new('RGB',(100,100),'white');drawer(ImageDraw.Draw(im));im.save(p);return p
    def test_outline_void_and_marker_unknown_diameter(self):
        def draw(d):
            d.rectangle((10,10,90,90),outline='black',width=2)
            d.rectangle((40,40,60,60),outline='black',width=2)
            d.ellipse((20,20,24,24),fill='red')
        p=self.fixture(draw);r=trace(p,(0,0,100,100))
        self.assertEqual(len(r['voids_px']),1)
        self.assertEqual(len(r['drill_markers']),1)
        self.assertIsNone(r['drill_markers'][0]['diameter_mm'])
        self.assertGreater(area(r['outline_px']),6000)
    def test_tabs_and_thin_notch_are_retained(self):
        pts=[(10,10),(40,10),(40,15),(50,15),(50,10),(90,10),(90,90),(10,90)]
        p=self.fixture(lambda d:d.line(pts+[pts[0]],fill='black',width=2))
        r=trace(p,(0,0,100,100))
        self.assertGreater(len(r['outline_px']),4)
        self.assertLess(area(r['outline_px']),6600)
    def test_open_contour_is_rejected(self):
        p=self.fixture(lambda d:d.line([(10,10),(90,10),(90,90)],fill='black',width=2))
        with self.assertRaisesRegex(SceneError,'No closed outline'):trace(p,(0,0,100,100))
