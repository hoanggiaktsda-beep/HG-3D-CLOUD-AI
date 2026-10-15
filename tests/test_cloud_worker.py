"""Negative checks: never substitute missing OCR, source evidence, or failed QA."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cloud_worker_sample', ROOT / 'scripts/cloud_worker_sample.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class CloudWorkerTests(unittest.TestCase):
    def test_real_ocr_labels_convert_units_without_nominal_inch_thickness(self):
        dimensions = worker.dimensions_from_ocr('(15” tall x 9.5” square)', '18.5 (3/4”) nominal')
        self.assertAlmostEqual(dimensions['width'], 241.3)
        self.assertAlmostEqual(dimensions['height'], 381)
        self.assertEqual(dimensions['thickness'], 18.5)

    def test_missing_ocr_fails_without_fallback(self):
        for text in ['', 'unreadable', '(15 tall x square)']:
            with self.assertRaises(ValueError):
                worker.dimensions_from_ocr(text, '18.5 (nominal)')
        with self.assertRaises(ValueError):
            worker.dimensions_from_ocr('(0” tall x 9.5” square)', '18.5 (nominal)')

    def test_changed_public_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            worker.verified_source(b'not the licensed source PDF')

    def test_envelope_error_is_rejected_even_when_rows_claim_pass(self):
        qa = dict(objects=[dict(pass_=True) for _ in range(5)], drill_markers=16, glb_drill_markers=16,
                  physical_drill_bores=0, render_executed=False)
        for row in qa['objects']:
            row.update({'pass': True, 'world_vertices_m': [[0, 0, 0], [.2413, .240, .381]]})
        with self.assertRaisesRegex(ValueError, 'Envelope'):
            worker.verify_qa(qa, dict(width=241.3, depth=241.3, height=381))
        qa['physical_drill_bores'] = 16
        with self.assertRaisesRegex(ValueError, 'Unknown bores'):
            worker.verify_qa(qa, dict(width=241.3, depth=241.3, height=381))


if __name__ == '__main__':
    unittest.main()
