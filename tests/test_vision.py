import copy,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from hgcloud.vision import normalize_response,prepare_request,ReplayProvider,ExternalVisionProvider,analyze,ROLES
from hgcloud.intake import receive,compile_scene
from hgcloud.core import SceneError
ROOT=Path(__file__).resolve().parents[1]

class VisionTests(unittest.TestCase):
    def setUp(self):
        self.response=json.loads((ROOT/'tests/fixtures/vision_response.json').read_text())
    def test_roles_preserved(self):
        self.assertEqual(len(ROLES),18);self.assertEqual(len(set(ROLES)),18)
    def test_model_cannot_self_confirm(self):
        item=self.response['objects'][0]['dimensions']['x']
        item.update(confidence='confirmed',basis='drawing',verified_by='model')
        result=normalize_response(self.response,'sha','offline_replay')
        self.assertEqual(result['objects'][0]['dimensions']['x']['confidence'],'needs_confirmation')
        self.assertNotIn('verified_by',result['objects'][0]['dimensions']['x'])
        self.assertEqual(item['confidence'],'confirmed')
    def test_model_cannot_invent_user_measurement(self):
        self.response['objects'][0]['dimensions']['x']['basis']='user_measurement'
        result=normalize_response(self.response,'sha','offline_replay')
        self.assertEqual(result['objects'][0]['dimensions']['x']['confidence'],'needs_confirmation')
    def test_invalid_response_rejected(self):
        for response in [{}, {'project':'p','objects':[]}, {'project':'p','objects':[{'kind':'python'}]}]:
            with self.subTest(response=response):
                with self.assertRaises(SceneError):normalize_response(response,'sha','offline_replay')
    def test_live_calls_disabled(self):
        with self.assertRaisesRegex(SceneError,'disabled'):ExternalVisionProvider().analyze({})
    def test_image_payload_and_response_binding(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='vision-test-') as td:
            folder=Path(td)/'intake'
            receive(ROOT/'tests/fixtures/dimensioned_cabinet.png','product_photo',folder)
            payload=prepare_request(folder/'intake.json','configured-model')
            self.assertTrue(payload['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
            result=analyze(folder/'intake.json',ReplayProvider(ROOT/'tests/fixtures/vision_response.json'))
            self.assertFalse(result['vision_provenance']['live_model_executed'])
            op=Path(td)/'observations.json';op.write_text(json.dumps(result))
            self.assertEqual(compile_scene(folder/'intake.json',op)['objects'][0]['confidence'],'inferred')
            result['vision_provenance']['source_sha256']='other-image';op.write_text(json.dumps(result))
            with self.assertRaisesRegex(SceneError,'different image'):compile_scene(folder/'intake.json',op)
    @unittest.skipUnless(shutil.which('blender') and shutil.which('tesseract'),'Blender and Tesseract required')
    def test_complete_replay_pipeline_and_unresolved_block(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='vision-e2e-') as td:
            def run(output,response):
                return subprocess.run(['python3','scripts/vision_pipeline.py','run','tests/fixtures/dimensioned_cabinet.png',
                    'technical_drawing',str(output),'--response-file',str(response)],cwd=ROOT,capture_output=True,text=True,timeout=180)
            output=Path(td)/'job'
            result=run(output,ROOT/'tests/fixtures/vision_response.json')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            state=json.loads((output/'pipeline.json').read_text())
            self.assertEqual(state['status'],'BUILT_NEEDS_REVIEW')
            self.assertEqual(state['geometry_status'],'PASS')
            self.assertTrue((output/'build/hg_scene.blend').is_file())
            self.assertTrue((output/'build/hg_scene.glb').is_file())
            self.response['objects'][0]['dimensions']['z']['value_mm']=None
            response=Path(td)/'missing.json';response.write_text(json.dumps(self.response))
            blocked=Path(td)/'blocked'
            result=run(blocked,response);self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads((blocked/'pipeline.json').read_text())['status'],'BLOCKED')
            self.assertFalse((blocked/'build').exists())
