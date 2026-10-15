"""Parser regression data only; actual recognition proof lives in Actions artifacts."""
import unittest
from hgcloud.core import SceneError
from hgcloud.model_dimensions import candidates_from_model_text, compare_candidates

HASH = 'a' * 64


class ModelDimensionTests(unittest.TestCase):
    def test_actual_trial_phrase_converts_units_without_trusted_geometry(self):
        result = candidates_from_model_text('common proportions (15" tall x 9.5" square)', HASH)
        self.assertAlmostEqual(result['dimensions']['x']['value_mm'], 241.3)
        self.assertAlmostEqual(result['dimensions']['y']['value_mm'], 241.3)
        self.assertEqual(result['dimensions']['z']['value_mm'], 381)
        self.assertEqual(result['source_sha256'], HASH)
        self.assertFalse(result['scene_ready'])
        self.assertFalse(result['build_allowed'])
        self.assertIsNone(result['center_mm'])
        self.assertTrue(all(value['confidence'] == 'needs_confirmation' and value['bbox_px'] is None for value in result['dimensions'].values()))

    def test_generic_units_not_design_specific_values(self):
        result = candidates_from_model_text('0.8 m tall × 45 cm square', HASH)
        self.assertEqual([result['dimensions'][axis]['value_mm'] for axis in 'xyz'], [450, 450, 800])
        result = candidates_from_model_text('850 mm tall x 950 mm square', HASH)
        self.assertEqual(result['dimensions']['y']['value_mm'], 950)

    def test_missing_units_depth_or_conflicting_text_does_not_get_filled(self):
        for text in ['15 tall x 9.5 square', '850 mm tall x 950 mm wide', 'a wooden chair',
                     '0 mm tall x 10 mm square', '-15" tall x 9.5" square', '1,950 mm tall x 950 mm square',
                     '15" tall x 9.5" square; 15" tall x 10" square']:
            with self.subTest(text=text), self.assertRaises(SceneError):
                candidates_from_model_text(text, HASH)
        with self.assertRaises(SceneError):
            candidates_from_model_text('15" tall x 9.5" square', 'wrong-image')

    def test_numeric_match_never_approves_build_and_mismatch_survives(self):
        result = candidates_from_model_text('850 mm tall x 912 mm square', HASH)
        comparison = compare_candidates(result, dict(x=950, y=950, z=850))
        self.assertEqual(comparison['errors_mm']['x'], -38)
        self.assertEqual(comparison['status'], 'NUMERICAL_MISMATCH')
        self.assertFalse(comparison['build_allowed'])
        match = compare_candidates(result, dict(x=912, y=912, z=850))
        self.assertIn('REVIEW_REQUIRED', match['status'])
        self.assertFalse(match['build_allowed'])
        self.assertEqual(compare_candidates(None, dict(x=950))['status'], 'NOT_COMPARABLE')
