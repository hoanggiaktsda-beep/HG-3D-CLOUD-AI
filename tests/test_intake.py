import copy,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from hgcloud.intake import receive,compile_scene
from hgcloud.core import SceneError,audit
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('tesseract'), 'Tesseract required')
class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='intake-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.intake=self.root/'intake'
        self.manifest=receive(ROOT/'tests/fixtures/dimensioned_cabinet.png','technical_drawing',self.intake)
        self.obs=json.loads((ROOT/'tests/fixtures/cabinet_observations.json').read_text())
    def compile(self):
        p=self.root/'observations.json';p.write_text(json.dumps(self.obs))
        return compile_scene(self.intake/'intake.json',p)
    def test_actual_ocr_candidates_are_unconfirmed(self):
        candidates=[r['dimension_candidate'] for r in self.manifest['ocr'] if 'dimension_candidate' in r]
        self.assertEqual({r['axis']:r['value_mm'] for r in candidates},{'x':1800,'y':450,'z':900})
        self.assertTrue(all(r['confidence']=='needs_confirmation' for r in candidates))
    def test_compile_preserves_per_axis_evidence_and_unknowns(self):
        obj=self.compile()['objects'][0]
        self.assertEqual(obj['size_mm'],[1800,450,900])
        self.assertEqual(obj['confidence'],'inferred')
        self.assertEqual(obj['kind'],'box')
        self.assertEqual(obj['dimension_evidence']['x']['confidence'],'confirmed')
        self.assertIn('Rear construction',obj['unknown_details'])
    def test_confirmed_envelope_with_unknown_structure_requires_review(self):
        self.obs['objects'][0]['placement_evidence']['confidence']='confirmed'
        scene=self.compile()
        self.assertEqual(scene['objects'][0]['confidence'],'confirmed')
        self.assertEqual(audit(scene)['status'],'NEEDS_REVIEW')
    def test_invalid_region_blocks(self):
        self.obs['objects'][0]['dimensions']['x']['bbox_px']=[0,0,2000,20]
        with self.assertRaisesRegex(SceneError,'reviewed image region'):self.compile()
    def test_missing_layout_height_blocks(self):
        del self.obs['objects'][0]['dimensions']['z']
        with self.assertRaisesRegex(SceneError,'missing dimension'):self.compile()
    def test_ocr_cannot_confirm(self):
        self.obs['objects'][0]['dimensions']['x']['basis']='ocr'
        with self.assertRaisesRegex(SceneError,'cannot confirm'):self.compile()
    def test_unreviewed_drawing_blocks(self):
        del self.obs['objects'][0]['dimensions']['x']['verified_by']
        with self.assertRaisesRegex(SceneError,'reviewed image region'):self.compile()
    def test_unresolved_dimension_blocks(self):
        self.obs['objects'][0]['dimensions']['x']['confidence']='needs_confirmation'
        with self.assertRaisesRegex(SceneError,'unresolved dimension'):self.compile()
    def test_inferred_dimension_is_not_promoted(self):
        self.obs['objects'][0]['dimensions']['y']['confidence']='inferred'
        self.assertEqual(self.compile()['objects'][0]['dimension_evidence']['y']['confidence'],'inferred')
    def test_source_tamper_blocks(self):
        (self.intake/'source.png').write_bytes(b'changed')
        with self.assertRaisesRegex(SceneError,'Source image changed'):self.compile()
    def test_invalid_values_block(self):
        for value in [0,-1,float('inf'),float('nan'),True]:
            with self.subTest(value=value):
                self.obs['objects'][0]['dimensions']['x']['value_mm']=value
                with self.assertRaises(SceneError):self.compile()
    def test_product_and_interior_intake(self):
        for kind in ['product_photo','interior_photo','layout']:
            m=receive(ROOT/'tests/fixtures/dimensioned_cabinet.png',kind,self.root/kind)
            self.assertFalse(m['automatic_geometry_recognition'])
            self.assertFalse(m['observations'])
    @unittest.skipUnless(shutil.which('blender'),'Blender required')
    def test_image_to_blend_measured_and_deviation_failure(self):
        scene=self.compile();sp=self.root/'scene.json';sp.write_text(json.dumps(scene));out=self.root/'build'
        def run(script):
            return subprocess.run(['blender','-b','-t','2','--python-exit-code','1','--python',str(ROOT/'scripts'/script),'--',str(sp),str(out)],cwd=ROOT,capture_output=True,text=True,timeout=120)
        result=run('blender_build.py');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        result=run('verify_blender.py');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads((out/'qa_report.json').read_text())
        self.assertEqual(report['geometry_status'],'PASS')
        self.assertEqual(report['status'],'NEEDS_REVIEW')
        self.assertTrue(report['evidence']['measured_dimensions_from_blender'])
        self.assertTrue(report['blender_details']['glb_created'])
        self.assertIn('1800',(out/'qa_report.html').read_text())
        scene['objects'][0]['size_mm'][0]+=10;sp.write_text(json.dumps(scene))
        result=run('verify_blender.py');self.assertNotEqual(result.returncode,0)
        self.assertEqual(json.loads((out/'qa_report.json').read_text())['status'],'QA_FAILED')
