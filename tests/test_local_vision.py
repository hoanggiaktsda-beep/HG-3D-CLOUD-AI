"""Contract/negative tests only. These fixtures are NOT image recognition evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from hgcloud.core import SceneError
from hgcloud.intake import receive, compile_scene
from hgcloud.local_vision import parse_proposal
from hgcloud.vision import ROLES

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


if __name__ == '__main__':
    unittest.main()
