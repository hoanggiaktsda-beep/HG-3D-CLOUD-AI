import json, tempfile, unittest
from pathlib import Path
from hgcloud.core import load,validate,audit,SceneError,save_report
from hgcloud.jobs import create_job
from hgcloud.preview import build_html
ROOT=Path(__file__).resolve().parents[1]

class SceneTests(unittest.TestCase):
    def setUp(self):self.scene=load(ROOT/'examples/living_room.json')
    def test_load(self):self.assertEqual(len(self.scene['objects']),6)
    def test_status(self):self.assertEqual(audit(self.scene)['status'],'NEEDS_REVIEW')
    def test_duplicates(self):
        scene=json.loads(json.dumps(self.scene));scene['objects'].append(scene['objects'][0]);
        with self.assertRaises(SceneError):validate(scene)
    def test_units(self):
        scene=json.loads(json.dumps(self.scene));scene['units']='cm'
        with self.assertRaises(SceneError):validate(scene)
    def test_negative_dimensions(self):
        scene=json.loads(json.dumps(self.scene));scene['objects'][0]['size_mm'][0]=-20
        with self.assertRaises(SceneError):validate(scene)
    def test_confirmed_source(self):
        scene=json.loads(json.dumps(self.scene));scene['objects'][0]['source_note']=''
        with self.assertRaises(SceneError):validate(scene)
    def test_unknown_shape(self):
        scene=json.loads(json.dumps(self.scene));scene['objects'][0]['kind']='imaginary'
        with self.assertRaises(SceneError):validate(scene)
    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            rp=Path(d)/'report.json';save_report(self.scene,rp)
            hp=Path(d)/'report.html';build_html(rp,hp)
            self.assertIn('HG 3D CLOUD',hp.read_text(encoding='utf8'))
    def test_job_creation(self):
        with tempfile.TemporaryDirectory() as d:
            a=create_job(ROOT/'examples/living_room.json',d);b=create_job(ROOT/'examples/living_room.json',d)
            self.assertNotEqual(a,b);self.assertTrue((a/'job.json').exists())
    def test_injected_html_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            scene=json.loads(json.dumps(self.scene));scene['project']='<script>alert(1)</script>'
            rp=Path(d)/'a.json'; save_report(scene,rp)
            hp=Path(d)/'a.html';build_html(rp,hp)
            self.assertNotIn('<script>',hp.read_text(encoding='utf8'))
    def test_invalid_camera_and_light_settings_rejected(self):
        import copy
        for field, value in [('lens_mm', 0), ('lens_mm', -35), ('lens_mm', float('nan')), ('lens_mm', float('inf'))]:
            scene=copy.deepcopy(self.scene);scene['cameras'][0][field]=value
            with self.subTest(camera=value), self.assertRaises(SceneError):validate(scene)
        for value in [-1, 0, float('inf'), float('nan')]:
            scene=copy.deepcopy(self.scene);scene['lights'][0]['diameter_mm']=value
            with self.subTest(diameter=value), self.assertRaises(SceneError):validate(scene)

    def test_overflow_rejected(self):
        scene=json.loads(json.dumps(self.scene));scene['objects'][0]['size_mm'][0]=float('inf')
        with self.assertRaises(SceneError):validate(scene)

if __name__=='__main__':unittest.main()
