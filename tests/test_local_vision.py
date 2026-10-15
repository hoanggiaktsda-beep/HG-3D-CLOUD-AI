"""Contract/negative tests only. These fixtures are NOT image recognition evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from hgcloud.core import SceneError
from hgcloud.intake import receive, compile_scene
from hgcloud.local_vision import parse_proposal, image_candidates
from hgcloud.vision import ROLES
from scripts.public_vision_trial import compare_dimensions

ROOT = Path(__file__).resolve().parents[1]


class LocalVisionTests(unittest.TestCase):
    def setUp(self):
        self.response = json.loads((ROOT / 'tests/fixtures/vision_response.json').read_text())

    def test_model_cannot_promote_numbers_or_placement_even_when_inferred(self):
        obj = self.response['objects'][0]
        obj['dimensions']['x'].update(confidence='confirmed', basis='user_measurement', verified_by='model')
        result = parse_proposal(json.dumps(self.response), 'source-hash', [2400, 2400])
        self.assertEqual(len(result['vision_provenance']['roles']), 18)
        self.assertEqual(result['vision_provenance']['roles'], ROLES)
        self.assertFalse(result['vision_provenance']['live_model_executed'])
        for value in result['objects'][0]['dimensions'].values():
            self.assertEqual(value['confidence'], 'needs_confirmation')
            self.assertEqual(value['basis'], 'model_proposal')
            self.assertNotIn('verified_by', value)
        self.assertEqual(result['objects'][0]['placement_evidence']['confidence'], 'needs_confirmation')

    def test_missing_axis_null_and_invalid_values(self):
        missing = copy.deepcopy(self.response)
        del missing['objects'][0]['dimensions']['z']
        with self.assertRaises(SceneError):
            parse_proposal(json.dumps(missing), 'hash', [2400, 2400])
        for value in [float('nan'), float('inf'), -1, True, 100001, '950']:
            candidate = copy.deepcopy(self.response)
            candidate['objects'][0]['dimensions']['z']['value_mm'] = value
            with self.subTest(value=value), self.assertRaises(SceneError):
                parse_proposal(json.dumps(candidate), 'hash', [2400, 2400])
        self.response['objects'][0]['dimensions']['z']['value_mm'] = None
        result = parse_proposal(json.dumps(self.response), 'hash', [2400, 2400])
        self.assertIsNone(result['objects'][0]['dimensions']['z']['value_mm'])

    def test_malformed_hallucinated_code_and_bad_pixel_evidence_rejected(self):
        for raw in ['a wooden stool', 'import bpy', '{}', '[]', '{"objects": []}', 'x' * 100001]:
            with self.subTest(raw=raw[:30]), self.assertRaises(SceneError):
                parse_proposal(raw, 'hash', [100, 100])
        for bbox in [[0, 0, 9999, 9999], [1, 2, 0, 1], [0, 0, float('nan'), 50]]:
            self.response['objects'][0]['dimensions']['x']['bbox_px'] = bbox
            with self.assertRaises(SceneError):
                parse_proposal(json.dumps(self.response), 'hash', [100, 100])

    def test_unreviewed_ai_json_cannot_enter_blender_compiler(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'outputs', prefix='local-vlm-gate-') as folder:
            job = Path(folder) / 'job'
            intake = receive(ROOT / 'tests/fixtures/dimensioned_cabinet.png', 'product_photo', job)
            proposal = parse_proposal(json.dumps(self.response), intake['sha256'], [2400, 2400])
            observations = job / 'observations.json'
            observations.write_text(json.dumps(proposal))
            with self.assertRaisesRegex(SceneError, 'Build blocked'):
                compile_scene(job / 'intake.json', observations)
            self.assertFalse((job / 'build').exists())

    def test_missing_prediction_is_not_reported_as_zero_error(self):
        self.assertEqual(compare_dimensions(None, {'x': 950})['status'], 'NOT_COMPARABLE')
        obj = self.response['objects'][0]
        obj['dimensions']['x']['value_mm'] = 912
        obj['dimensions']['z']['value_mm'] = None
        comparison = compare_dimensions(self.response, {'x': 950, 'z': 850})
        self.assertEqual(comparison['rows'][0]['error_mm'], -38)
        self.assertIsNone(comparison['rows'][1]['error_mm'])
        self.assertIn('UNREVIEWED', comparison['status'])

    def test_empty_copied_template_cannot_be_claimed_as_geometry(self):
        for value in self.response['objects'][0]['dimensions'].values():
            value.update(value_mm=None, bbox_px=None)
        with self.assertRaisesRegex(SceneError, 'empty/template'):
            parse_proposal(json.dumps(self.response), 'hash', [2400, 2400])

    def test_detector_pixels_never_become_millimeters_or_buildable_objects(self):
        result = image_candidates([dict(label='chair', score=.9, bbox_px=[10, 20, 90, 95])], [100, 100])
        self.assertFalse(result['scene_ready'])
        self.assertFalse(result['build_allowed'])
        obj = result['objects'][0]
        self.assertEqual(obj['dimensions_mm'], dict(x=None, y=None, z=None))
        self.assertIsNone(obj['center_mm'])
        self.assertEqual(obj['bbox_px'], [10, 20, 90, 95])
        for entry in [dict(label='chair', score=float('nan'), bbox_px=[10, 20, 90, 95]),
                      dict(label='chair', score=.9, bbox_px=[10, 20, 190, 95])]:
            with self.assertRaises(SceneError):
                image_candidates([entry], [100, 100])


if __name__ == '__main__':
    unittest.main()
