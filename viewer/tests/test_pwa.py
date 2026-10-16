"""TEST32: Chromium screen/input emulation, not physical Apple/Windows hardware."""
import os,unittest,json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get('HG_VIEWER_URL','http://127.0.0.1:8792/HG-3D-CLOUD-AI/')
class PwaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(executable_path=__import__('shutil').which('chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 @classmethod
 def tearDownClass(cls): cls.browser.close();cls.p.stop()
 def page(self,**options):
  c=self.browser.new_context(accept_downloads=True,**options);self.addCleanup(c.close)
  p=c.new_page();p.goto(URL);p.evaluate("document.body.classList.remove('hg-minimal-ui')");p.wait_for_function('() => (window.hgViewer?.ready)');return p
 def test_platform_layout_downloads_and_controls(self):
  profiles=[('iphone',320,568,True,'iPhone'),('ipad',820,1180,True,'iPad'),('windows',1366,768,False,'Windows NT 10.0; Win64; x64'),('macos',1440,900,False,'Macintosh; Intel Mac OS X 14_0')]
  for name,w,h,touch,platform in profiles:
   with self.subTest(profile=name):
    p=self.page(viewport={'width':w,'height':h},is_mobile=touch,has_touch=touch,user_agent=f'Mozilla/5.0 ({platform}) AppleWebKit/537.36 Chrome/150.0.0.0 Safari/537.36')
    self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'),w)
    p.locator('[data-view=back]').click();self.assertEqual(p.evaluate('hgViewer.currentView'),'back')
    before=p.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)');p.locator('#zoom-out').click()
    self.assertGreater(p.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)'),before)
    p.locator('#model-instruction').fill('Kiểm tra TEST 32; không gửi dữ liệu')
    self.assertTrue(p.locator('#create-job').is_disabled())
    self.assertIn('Chưa có công việc',p.locator('#job-state').inner_text())
    self.assertEqual(p.locator('#object-rows tr').count(),8)
    for ext in ['glb','blend']:
     with p.expect_download() as pending:p.locator(f'a[href="assets/sample.{ext}"]').click()
     download=pending.value;self.assertIsNone(download.failure())
     self.assertEqual(hashlib.sha256(Path(download.path()).read_bytes()).hexdigest(),hashlib.sha256((ROOT/f'viewer/assets/sample.{ext}').read_bytes()).hexdigest())
    p.screenshot(path=str(ROOT/f'outputs/test32/{name}.png'),full_page=True)
    p.set_viewport_size({'width':h,'height':w});self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'),h)
 def test_offline_public_cache_and_private_draft_not_persisted(self):
  p=self.page(viewport={'width':390,'height':844})
  p.wait_for_function('() => (navigator.serviceWorker.controller !== null)',timeout=30000)
  p.locator('#source-images').set_input_files(ROOT/'tests/fixtures/dimensioned_cabinet.png')
  p.wait_for_function('() => (document.querySelectorAll("#image-previews img").length===1)')
  p.locator('#model-instruction').fill('PRIVATE-SENTINEL-TEST32')
  data=p.evaluate('''async()=>({scope:(await navigator.serviceWorker.ready).scope,keys:(await Promise.all((await caches.keys()).map(async k=>(await (await caches.open(k)).keys()).map(r=>r.url)))).flat(),local:localStorage.length,session:sessionStorage.length})''')
  self.assertEqual(data['scope'],URL)
  manifest=json.loads((ROOT/'viewer/dist/build-manifest.json').read_text())
  allowed={URL+f['path'] for f in manifest['files']}
  self.assertTrue(data['keys']);self.assertTrue(set(data['keys'])<=allowed)
  self.assertFalse(any('blob:' in x or x.endswith('.blend') or '?' in x for x in data['keys']))
  self.assertEqual((data['local'],data['session']),(0,0))
  p.context.set_offline(True);p.reload();p.wait_for_function('() => (hgViewer.ready)')
  self.assertEqual(p.locator('#height').inner_text(),'850')
  self.assertEqual(p.locator('#model-instruction').input_value(),'')
  self.assertEqual(p.locator('#image-previews img').count(),0)
  self.assertEqual(p.locator('#connection-state').inner_text(),'CHƯA KẾT NỐI')
  self.assertFalse(p.evaluate('''async()=>{try{await fetch('./assets/sample.blend');return true}catch{return false}}'''))
 def test_manifest_security_and_worker_link(self):
  p=self.page();violations=[];p.on('console',lambda m:violations.append(m.text) if 'Content Security Policy' in m.text else None)
  manifest=p.evaluate("async()=>await (await fetch('./manifest.webmanifest')).json()")
  self.assertEqual(manifest['scope'],'./');self.assertEqual(manifest['start_url'],'./')
  self.assertEqual(manifest['display'],'standalone');self.assertEqual({i['sizes'] for i in manifest['icons']},{'192x192','512x512'})
  self.assertEqual(p.locator('#worker-link').get_attribute('href'),'https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/workflows/test31-cloud-jobs.yml')
  self.assertEqual(p.locator('#worker-link').get_attribute('rel'),'noopener noreferrer')
  csp=p.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute('content')
  for rule in ["connect-src 'self'","form-action 'none'","object-src 'none'","base-uri 'none'"]:self.assertIn(rule,csp)
  self.assertNotIn("'unsafe-inline'",csp)
  self.assertTrue(p.locator('#install-app').is_hidden()) # no invented install success in headless mode
  self.assertEqual(violations,[])
