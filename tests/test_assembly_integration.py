"""Protocol fixtures and real CV/Blender regression, NOT AI recognition evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image, ImageDraw
from hgcloud.core import SceneError
from hgcloud.assembly_evidence import parse_sheet, parse_thickness, parse_legend, parse_total, verified_reading, agree_calibration
from hgcloud.cut_layout import extract_layout
from hgcloud.cut_layout_qa import verify_projection

ROOT = Path(__file__).resolve().parents[1]


class AssemblyIntegrationTests(unittest.TestCase):
    def test_read_retry_is_bounded_and_has_no_ocr_or_answer_input(self):
        from scripts.public_assembly_trial import read_pixels
        class ProtocolOnlyFixture:
            def __init__(self, values):
                self.values = iter(values)
                self.calls = []
            def generate(self, image, prompt, budget):
                self.calls.append((image, prompt, budget))
                return next(self.values), 1
        fixture = ProtocolOnlyFixture(['system', 'Original printed text'])
        text, attempts = read_pixels(fixture, self.image, 'parts_table')
        self.assertEqual(text, 'Original printed text')
        self.assertEqual([a['text'] for a in attempts], ['system', 'Original printed text'])
        self.assertEqual(len(fixture.calls), 2)
        self.assertTrue(all(c[0] is self.image for c in fixture.calls))
        fixture = ProtocolOnlyFixture(['system', 'system'])
        text, attempts = read_pixels(fixture, self.image, 'parts_table')
        self.assertEqual(text, 'system')
        self.assertEqual(len(attempts), 2)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'outputs', prefix='assembly-regression-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.image = self.folder / 'synthetic.png'
        image = Image.new('RGB', (500, 700), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 170, 440, 650), outline='black', width=1)
        draw.rectangle((105, 200, 235, 390), outline='red', width=2)
        draw.rectangle((145, 260, 190, 300), outline='cyan', width=2)
        polygon = [(270, 410), (410, 410), (410, 610), (320, 610), (320, 520), (270, 520), (270, 410)]
        draw.line(polygon, fill='red', width=2)
        for x, y in [(125, 220), (350, 440)]:
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(0, 170, 0))
        image.save(self.image)
        self.calibration = dict(sheet_mm=[360, 480], thickness_mm=12, part_count=2,
                                legend=dict(outside='red', inside='cyan', drill='green'))

    def test_unit_parsers_require_explicit_dimensions_and_unambiguous_roles(self):
        self.assertEqual(parse_sheet("single 3'x6' sheet"), (914.4000000000001, 1828.8000000000002))
        self.assertEqual(parse_thickness('cut files scaled for 12mm'), 12)
        self.assertEqual(parse_total('Total per File 2 123 + 4 holes'), 2)
        for text in ['use a standard sheet', '3x6 material', "3'x6' or 4'x8' sheet"]:
            with self.assertRaises(SceneError):
                parse_sheet(text)
        with self.assertRaises(SceneError):
            parse_thickness('3/4 inch material')
        with self.assertRaises(SceneError):
            parse_legend('Red lines = outside cuts')

    def records(self):
        # Simulated protocol records ONLY to test the gate; never used in live workflow.
        digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        texts = dict(cut_context="DIGITAL CUT FILE single 3'x6' sheet\nRed Lines = outside cuts\nCyan Lines = inside cuts\nGreen Circles = drilled holes",
                     material='Cut files provided are scaled for 12mm', parts_table='Total per File 2 123 + 4 holes')
        return [dict(purpose=purpose, image_path=str(self.image), image_sha256=digest, ocr_image_sha256=digest,
                     document_sha256='f' * 64, ai_text=text, ocr_text=text,
                     execution=dict(live_model_executed=True, backend='qwen2vl_cpu_live',
                                    model_revision='895c3a49bc3fa70a340399125c650a463535e71c', image_sha256=digest))
                for purpose, text in texts.items()]

    def test_agreement_does_not_authorize_assembly_or_final_approval(self):
        records = self.records()
        result = agree_calibration(records, 'f' * 64)
        self.assertFalse(result['assembly_allowed'])
        self.assertEqual(result['status'], 'CẦN XÁC NHẬN')
        self.assertEqual(result['scope'], 'unassembled_cut_layout_only')
        records[1]['ai_text'] = 'Cut files scaled for 13mm'
        with self.assertRaisesRegex(SceneError, 'disagree'):
            agree_calibration(records, 'f' * 64)
        with self.assertRaisesRegex(SceneError, 'missing'):
            agree_calibration(self.records()[:2], 'f' * 64)

    def test_replay_mixed_source_and_changed_image_are_rejected(self):
        for field, value in [('live_model_executed', False), ('backend', 'offline_replay'), ('image_sha256', 'wrong')]:
            record = self.records()[0]
            record['execution'][field] = value
            with self.subTest(field=field), self.assertRaises(SceneError):
                verified_reading(record, 'f' * 64)
        with self.assertRaisesRegex(SceneError, 'Mixed'):
            verified_reading(self.records()[0], 'a' * 64)

    def test_actual_contours_slots_markers_counts_and_scale_guard(self):
        layout = extract_layout(self.image, self.calibration)
        self.assertEqual(len(layout['parts']), 2)
        self.assertEqual(sum(len(p['voids_mm']) for p in layout['parts']), 1)
        self.assertEqual(sum(len(p['drill_markers_xy_mm']) for p in layout['parts']), 2)
        self.assertFalse(layout['assembly_allowed'])
        self.assertTrue(all(p['assembly_position_mm'] is None and p['drill_diameter_mm'] is None for p in layout['parts']))
        with self.assertRaises(SceneError):
            extract_layout(self.image, dict(self.calibration, part_count=3))
        with self.assertRaises(SceneError):
            extract_layout(self.image, dict(self.calibration, sheet_mm=[360, 440]))
        image = Image.open(self.image)
        ImageDraw.Draw(image).line((150, 200, 165, 200), fill='white', width=5)
        image.save(self.image)
        with self.assertRaises(SceneError):
            extract_layout(self.image, self.calibration)

    @unittest.skipUnless(shutil.which('blender'), 'Actual Blender required')
    def test_actual_blend_glb_per_part_and_projection_detect_bad_placement(self):
        spec = extract_layout(self.image, self.calibration)
        spec_path = self.folder / 'spec.json'
        spec_path.write_text(json.dumps(spec))
        builder = ROOT / 'scripts/blender_cut_layout.py'
        def run(script, out):
            return subprocess.run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(script), '--', str(spec_path), str(out)],
                                  cwd=ROOT, capture_output=True, text=True, timeout=120)
        out = self.folder / 'good'
        result = run(builder, out)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((out / 'cut_layout.blend').is_file())
        self.assertEqual((out / 'cut_layout.glb').read_bytes()[:4], b'glTF')
        qa = json.loads((out / 'part_qa.json').read_text())
        projection = verify_projection(spec, qa)
        self.assertGreater(projection['min_iou'], .97)
        self.assertEqual(qa['physical_drill_bores'], 0)
        self.assertEqual(qa['drill_markers'], 2)
        bad = copy.deepcopy(qa)
        for triangle in bad['parts'][0]['top_triangles_mm']:
            for point in triangle:
                point[0] += 20
        with self.assertRaisesRegex(SceneError, 'silhouette mismatch'):
            verify_projection(spec, bad)
        broken = self.folder / 'broken.py'
        broken.write_text(builder.read_text().replace('ob.location = Vector(part[\'center_mm\']) / 1000',
                                                     'ob.location = Vector(part[\'center_mm\']) / 1000 + Vector((.01, 0, 0))'))
        result = run(broken, self.folder / 'bad')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
