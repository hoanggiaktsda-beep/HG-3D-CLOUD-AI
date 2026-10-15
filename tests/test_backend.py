import io,json,os,secrets,tempfile,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from hgcloud.backend.api import create_app
from hgcloud.backend.store import Store
from hgcloud.backend.worker import run_once
from hgcloud.backend.vision_adapter import configure_provider,VisionUnavailable
ROOT=Path(__file__).resolve().parents[1]
class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='private-api-test-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'storage'
        self.tokens={'alice':secrets.token_urlsafe(40),'bob':secrets.token_urlsafe(40)}
        self.app=create_app(self.root,self.tokens);self.client=TestClient(self.app)
        self.auth={'Authorization':'Bearer '+self.tokens['alice']};self.bob={'Authorization':'Bearer '+self.tokens['bob']}
    def upload(self,headers=None):
        return self.client.post('/jobs',headers=headers or self.auth,data={'input_type':'technical_drawing','instruction':'Read printed dimensions, never render'},files={'image':('../../private.py', (ROOT/'tests/fixtures/dimensioned_cabinet.png').read_bytes(),'image/png')})
    def observations(self):return json.loads((ROOT/'tests/fixtures/cabinet_observations.json').read_text())
    def test_auth_fail_closed_and_ownership(self):
        self.assertEqual(self.client.get('/jobs').status_code,401)
        self.assertEqual(self.client.get('/jobs',headers={'Authorization':'Bearer bad'}).status_code,401)
        r=self.upload();self.assertEqual(r.status_code,201);jid=r.json()['id']
        self.assertEqual(self.client.get('/jobs/'+jid,headers=self.bob).status_code,404)
        self.assertEqual(self.client.get('/jobs/'+jid+'/source',headers=self.bob).status_code,404)
        self.assertEqual(self.client.post('/jobs/'+jid+'/observations',headers=self.bob,json=self.observations()).status_code,404)
        self.assertEqual(self.client.get('/jobs',headers=self.bob).json(),[])
        self.assertFalse((self.root/'private.py').exists());self.assertEqual(self.root.stat().st_mode&0o777,0o700)
    def test_invalid_images_and_unknown_artifacts(self):
        r=self.client.post('/jobs',headers=self.auth,data={'input_type':'layout'},files={'image':('fake.png',b'<svg/>','image/png')})
        self.assertEqual(r.status_code,422)
        r=self.client.get('/jobs/'+'a'*32+'/artifacts/glb',headers=self.auth);self.assertEqual(r.status_code,404)
        jid=self.upload().json()['id']
        self.assertEqual(self.client.get('/jobs/'+jid+'/artifacts/glb',headers=self.auth).status_code,409)
        self.assertEqual(self.client.get('/jobs/'+jid+'/artifacts/credentials',headers=self.auth).status_code,404)
    def test_missing_dimensions_block_and_double_submission_conflicts(self):
        jid=self.upload().json()['id'];obs=self.observations();del obs['objects'][0]['dimensions']['z']
        self.assertEqual(self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=obs).status_code,422)
        self.assertEqual(self.app.state.store.get(jid)['state'],'WAITING_ANALYSIS')
        self.assertEqual(self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json={'objects':[None]}).status_code,422)
        self.assertEqual(self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=self.observations()).status_code,202)
        self.assertEqual(self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=self.observations()).status_code,409)
    def test_durable_queue_claims_once(self):
        jid=self.upload().json()['id'];self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=self.observations())
        store=Store(self.root)
        with ThreadPoolExecutor(max_workers=2) as pool:claimed=list(pool.map(lambda _:store.claim(),range(2)))
        self.assertEqual(sum(v is not None for v in claimed),1)
        self.assertEqual(Store(self.root).get(jid)['state'],'RUNNING')
    def test_real_blender_and_private_download_revision(self):
        jid=self.upload().json()['id'];self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=self.observations())
        self.assertTrue(run_once(self.app.state.store))
        state=self.client.get('/jobs/'+jid,headers=self.auth).json();self.assertEqual(state['state'],'NEEDS_REVIEW')
        glb=self.client.get('/jobs/'+jid+'/artifacts/glb',headers=self.auth);self.assertEqual(glb.content[:4],b'glTF')
        blend=self.client.get('/jobs/'+jid+'/artifacts/blend',headers=self.auth);self.assertTrue(blend.content.startswith(b'BLENDER'))
        qa=self.client.get('/jobs/'+jid+'/artifacts/qa',headers=self.auth).json()
        self.assertEqual(qa['geometry_status'],'PASS');self.assertEqual(qa['status'],'NEEDS_REVIEW')
        self.assertFalse(qa['automatic_vision_executed'])
        self.assertEqual(self.client.get('/jobs/'+jid+'/artifacts/glb',headers=self.bob).status_code,404)
        new=self.client.post('/jobs/'+jid+'/revisions',headers=self.auth,json={'instruction':'Adjust from new evidence, do not invent hidden parts'})
        self.assertEqual(new.status_code,201);self.assertNotEqual(new.json()['id'],jid)
        self.assertEqual(new.json()['state'],'WAITING_ANALYSIS')
        self.assertEqual(self.app.state.store.get(jid)['state'],'NEEDS_REVIEW')
    def test_cors_tokens_limits_and_vision_truth(self):
        r=self.client.get('/capabilities',headers=self.auth|{'Origin':'https://evil.example'})
        self.assertNotIn('access-control-allow-origin',r.headers);self.assertFalse(r.json()['vision'])
        self.assertEqual(len(r.json()['roles']),18)
        with self.assertRaises(VisionUnavailable):configure_provider().analyze(b'private','layout','test')
        with self.assertRaises(ValueError):create_app(self.root,{'user':'short'})
        with self.assertRaises(ValueError):create_app(self.root,{'a':self.tokens['alice'],'b':self.tokens['alice']})
        r=self.client.post('/jobs',headers=self.auth|{'Content-Length':str(30*1024*1024)},content=b'')
        self.assertEqual(r.status_code,413)

    def test_auth_happens_before_body_parsing_and_quota_is_atomic(self):
        r=self.client.post('/jobs',content=b'bad multipart',headers={'Content-Type':'multipart/form-data; boundary=x'})
        self.assertEqual(r.status_code,401)
        for _ in range(20):self.app.state.store.create('alice',{'instruction':'quota test'})
        self.assertEqual(self.upload().status_code,429)
    def test_failed_worker_never_exposes_partial_artifacts(self):
        from unittest.mock import patch
        jid=self.upload().json()['id']
        self.client.post('/jobs/'+jid+'/observations',headers=self.auth,json=self.observations())
        with patch('hgcloud.backend.worker.command',side_effect=RuntimeError('test worker failure')):
            run_once(self.app.state.store)
        self.assertEqual(self.app.state.store.get(jid)['state'],'FAILED')
        self.assertEqual(self.client.get('/jobs/'+jid+'/artifacts/glb',headers=self.auth).status_code,409)
