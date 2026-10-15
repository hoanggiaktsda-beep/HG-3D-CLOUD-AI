"""Synthetic regression fixtures only; NOT public-image recognition evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
from PIL import Image, ImageDraw
from hgcloud.assembly_constraints import rigid_transform, assembly_gate, instruction_relations, labelled_parts, require_complete_pages, metric_label
from hgcloud.core import SceneError

ROOT = Path(__file__).resolve().parents[1]


class AssemblyConstraintTests(unittest.TestCase):
    def test_full_document_coverage_and_rotated_metric_label_ranges(self):
        require_complete_pages(7, [1, 2, 3, 4, 5, 6, 7])
        with self.assertRaises(SceneError):
            require_complete_pages(7, [4, 5, 6, 7])
        self.assertEqual(metric_label('d = 37.2 CM')['value_mm'], 372)
        label = metric_label('w=60—160CM')
        self.assertIsNone(label['value_mm'])
        self.assertEqual(label['range_mm'], [600, 1600])
        with self.assertRaises(SceneError):
            metric_label('use a standard width')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'outputs', prefix='test30-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.image = self.folder / 'fixture.png'
        Image.new('RGB', (200, 200), 'white').save(self.image)
        self.digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.part = dict(id='fixture_a', outline_mm=[[-10, -10], [10, -10], [10, 10], [-10, 10]],
                         thickness_mm=20, center_mm=[40, 40, 10], voids_mm=[], drill_markers_xy_mm=[])
        self.layout = dict(schema='hg_cut_layout_v1', source=str(self.image), source_sha256=self.digest,
                           scope='unassembled_cut_layout_only', assembly_allowed=False, source_uncertainty_mm=1,
                           parts=[self.part], calibration={})

    def proposal(self, part, center):
        anchors = [[-10, -10, -part['thickness_mm'] / 2], [10, -10, -part['thickness_mm'] / 2], [-10, 10, part['thickness_mm'] / 2]]
        result = dict(source_sha256=self.digest, semantic_assignment_status='confirmed', semantic_label='SYNTHETIC FIXTURE',
                      anchor_review_status='confirmed', anchor_source_note='SYNTHETIC protocol fixture, no AI/image proof',
                      local_anchors_mm=anchors, world_anchors_mm=(np.asarray(anchors) + center).tolist(),
                      tolerance_mm=.1, views={})
        for name, axes in [('top', [0, 1]), ('front', [0, 2]), ('side', [1, 2])]:
            image = self.folder / (name + '.png')
            im = Image.new('RGB', (200, 200), 'white')
            ImageDraw.Draw(im).text((10, 10), 'SYNTHETIC ' + name, fill='black')
            im.save(image)
            half = [10, 10, part['thickness_mm'] / 2]
            result['views'][name] = dict(image_path=str(image), image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                                        document_sha256=self.digest,
                                        status='confirmed', basis='reviewed_metric_annotation', source_note='SYNTHETIC annotated-view fixture',
                                        bbox_mm=[center[i] - half[i] for i in axes] + [center[i] + half[i] for i in axes])
        return result

    def test_rigid_orientation_position_and_reject_underconstrained_or_scaled(self):
        local = [[0, 0, 0], [10, 0, 0], [0, 20, 0], [0, 0, 15]]
        rotation = np.asarray([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        world = np.asarray(local) @ rotation.T + [100, 50, 30]
        r, t, error = rigid_transform(local, world, .01)
        np.testing.assert_allclose(r, rotation, atol=1e-10)
        np.testing.assert_allclose(t, [100, 50, 30])
        self.assertLess(error, 1e-10)
        for bad_a, bad_b in [([[0, 0, 0], [1, 0, 0], [2, 0, 0]], [[0, 0, 0], [1, 0, 0], [2, 0, 0]]),
                             (local, np.asarray(local) * 2), (local, np.asarray(local) * [-1, 1, 1])]:
            with self.assertRaises(SceneError):
                rigid_transform(bad_a, bad_b, .01)

    def test_gate_missing_views_bad_mapping_changed_image_and_contradiction(self):
        proposal = self.proposal(self.part, [0, 0, 10])
        plan = dict(placements={'fixture_a': proposal})
        result = assembly_gate(self.layout, plan)
        self.assertTrue(result['complete_placement_evidence'])
        self.assertFalse(result['final_approved'])
        self.assertEqual(len(result['roles']), 18)
        for change in ['missing_view', 'bad_mapping', 'inferred', 'changed_image', 'wrong_position', 'mixed_document']:
            bad = copy.deepcopy(plan)
            p = bad['placements']['fixture_a']
            if change == 'missing_view': del p['views']['side']
            if change == 'bad_mapping': p['semantic_assignment_status'] = 'inferred'
            if change == 'inferred': p['views']['front']['status'] = 'inferred'
            if change == 'changed_image': p['views']['front']['image_sha256'] = 'wrong'
            if change == 'wrong_position': p['views']['front']['bbox_mm'][0] += 5
            if change == 'mixed_document': p['views']['front']['document_sha256'] = 'another drawing'
            with self.subTest(change=change):
                self.assertEqual(assembly_gate(self.layout, bad)['status'], 'BLOCKED_COMPLETE_ASSEMBLY')
        self.assertFalse(assembly_gate(dict(self.layout, parts=[]), {})['complete_placement_evidence'])

    def test_ocr_instruction_order_is_not_metric_placement(self):
        text = 'Slot part B into part D. Fit side parts C, then part E.'
        relations = instruction_relations(text)
        self.assertEqual([r['parts'] for r in relations], [['B', 'D'], ['C', 'E']])
        self.assertTrue(all(r['metric_transform'] is None for r in relations))
        result = assembly_gate(self.layout, dict(relations=relations))
        self.assertEqual(len(result['blocked_parts']), 1)
        self.assertFalse(result['next_test_allowed'])
        rows = labelled_parts('A Seat Back 1 64\nB Seat 1 98\nCc Sides 2 249\nTotal per Chair 10 619 + 28 holes')
        self.assertEqual([(r['label'], r['quantity']) for r in rows], [('A', 1), ('B', 1), ('C', 2)])
        self.assertTrue(all(r['contour_assignment'] is None for r in rows))

    def run_worker(self, parts, centers, name):
        spec = dict(self.layout, parts=parts)
        spec_path = self.folder / (name + '-spec.json')
        spec_path.write_text(json.dumps(spec))
        base = self.folder / (name + '-base')
        def blender(script, args):
            result = subprocess.run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(ROOT / 'scripts' / script), '--', *map(str, args)],
                                    capture_output=True, text=True, cwd=ROOT, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        blender('blender_cut_layout.py', [spec_path, base])
        plan_path = self.folder / (name + '-plan.json')
        plan_path.write_text(json.dumps(dict(placements={p['id']: self.proposal(p, c) for p, c in zip(parts, centers)})))
        out = self.folder / name
        blender('blender_assembly_review.py', [base / 'cut_layout.blend', spec_path, plan_path, out])
        return json.loads((out / 'assembly_qa.json').read_text()), out

    @unittest.skipUnless(shutil.which('blender'), 'Real Blender required')
    def test_actual_blender_rotated_plate_keeps_thickness_and_world_orientation(self):
        rotated = dict(self.part, id='rotated_fixture', thickness_mm=10, center_mm=[40, 40, 5],
                       outline_mm=[[-20, -10], [20, -10], [20, 10], [-20, 10]])
        original = self.proposal
        def fixture_proposal(part, center):
            result = original(part, center)
            result['local_anchors_mm'] = [[-20, -10, -5], [20, -10, -5], [-20, 10, 5]]
            result['world_anchors_mm'] = [[30, 5, -5], [70, 5, -5], [30, -5, 15]]
            for view, box in [('top', [30, -5, 70, 5]), ('front', [30, -5, 70, 15]), ('side', [-5, -5, 5, 15])]:
                result['views'][view]['bbox_mm'] = box
            return result
        self.proposal = fixture_proposal
        qa, _ = self.run_worker([rotated], [[50, 0, 5]], 'rotated')
        self.assertEqual(qa['technical_status'], 'PASS_MESH_CHECKS_ONLY')
        row = qa['parts'][0]
        np.testing.assert_allclose(row['actual_local_mm'], [40, 20, 10], atol=.001)
        np.testing.assert_allclose(row['world_bbox_mm'], [[30, -5, -5], [70, 5, 15]], atol=.001)
        self.assertLess(row['orientation_error'], 1e-6)
        self.assertLess(row['glb_bbox_error_mm'], .001)

    @unittest.skipUnless(shutil.which('blender'), 'Real Blender required')
    def test_actual_blender_containment_is_a_collision_not_a_clearance_pass(self):
        inner = dict(self.part, id='fixture_b', center_mm=[100, 100, 10])
        inner['outline_mm'] = [[-10, -10], [10, -10], [10, 10], [-10, 10]]
        outer = dict(self.part)
        outer['outline_mm'] = [[-30, -30], [30, -30], [30, 30], [-30, 30]]
        # Inner exactly fits the outer thickness but has no intersecting boundary faces.
        # Surface-overlap-only collision tests can miss this containment case.
        # Override synthetic outer views with their actual known fixture extents.
        original = self.proposal
        def fixture_proposal(part, center):
            result = original(part, center)
            if part['id'] == 'fixture_a':
                result['views']['top']['bbox_mm'] = [-30, -30, 30, 30]
                result['views']['front']['bbox_mm'] = [-30, -10, 30, 10]
                result['views']['side']['bbox_mm'] = [-30, -10, 30, 10]
            return result
        self.proposal = fixture_proposal
        qa, _ = self.run_worker([outer, inner], [[0, 0, 0], [0, 0, 0]], 'containment')
        self.assertEqual(qa['technical_status'], 'FAIL')
        self.assertAlmostEqual(qa['pair_checks'][0]['intersection_volume_mm3'], 8000, delta=1)
        self.assertFalse(qa['final_approved'])

    @unittest.skipUnless(shutil.which('blender'), 'Real Blender required')
    def test_actual_blender_gap_reopen_and_no_hardware_fabrication(self):
        other = dict(self.part, id='fixture_b', center_mm=[100, 100, 10])
        qa, out = self.run_worker([self.part, other], [[0, 0, 10], [25, 0, 10]], 'gap')
        self.assertEqual(qa['technical_status'], 'PASS_MESH_CHECKS_ONLY')
        pair = qa['pair_checks'][0]
        self.assertFalse(pair['collision'])
        self.assertAlmostEqual(pair['gap_lower_mm'], 5, delta=.001)
        self.assertAlmostEqual(pair['gap_upper_mm'], 5, delta=.001)
        self.assertEqual(qa['physical_hardware_added'], 0)
        self.assertEqual(qa['blend_reopen'], 'PASS')
        self.assertEqual(qa['glb_reimport'], 'PASS')
        self.assertTrue((out / 'assembly_candidate.blend').is_file())
        self.assertEqual((out / 'assembly_candidate.glb').read_bytes()[:4], b'glTF')
        self.assertFalse(qa['final_approved'])


if __name__ == '__main__':
    unittest.main()
