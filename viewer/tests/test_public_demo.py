"""Actual public release is optional before first inference; never fabricate one."""
import os,json,unittest,hashlib,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get('HG_VIEWER_URL','http://127.0.0.1:8794/HG-3D-CLOUD-AI/')
class PublicDemoBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def page(self,width):
  c=self.browser.new_context(viewport={'width':width,'height':900},accept_downloads=True);self.addCleanup(c.close)
  p=c.new_page();p.goto(URL);p.evaluate("document.body.classList.remove('hg-minimal-ui')");p.wait_for_function('()=>hgViewer.ready');p.wait_for_function('()=>!document.querySelector("#public-demo-status").textContent.startsWith("Đang đọc")');return p
 def test_public_workflow_link_is_native_auth_without_customer_upload(self):
  p=self.page(390)
  self.assertEqual(p.locator('#run-public-demo').get_attribute('href'),'https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/workflows/public-demo.yml')
  self.assertTrue(p.locator('#create-job').is_disabled());self.assertIn('CHƯA KẾT NỐI',p.locator('#connection-state').inner_text())
  self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'),390)
  self.assertFalse(p.evaluate('hgPublicDemo.ready'))
 def test_public_result_is_only_shown_from_available_verified_release(self):
  p=self.page(1440);path=ROOT/'viewer/public-demo/release.json'
  if not path.exists():
   self.assertIn('Chưa có kết quả AI công khai',p.locator('#public-demo-status').inner_text())
   self.assertEqual(p.locator('#public-demo-cases button').count(),0);return
  release=json.loads(path.read_text());self.assertEqual(p.locator('#public-demo-cases article').count(),3)
  for record in release['cases']:
   if record['id']=='chair' and record['status']=='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW':
    p.get_by_role('button',name='Xem kết quả AI 3D',exact=True).click();p.wait_for_function('()=>hgPublicDemo.ready')
    self.assertEqual(p.evaluate('hgPublicDemo.meshes'),record['parts'])
    self.assertEqual(p.evaluate('hgPublicDemo.run_id'),release['run_id'])
    self.assertIn('Chưa lắp ráp',p.locator('#public-demo-status').inner_text())
    for ext in ['GLB','BLEND']:
     with p.expect_download() as event:p.locator('#public-demo-cases').get_by_role('link',name='Tải '+ext,exact=True).click()
     dl=event.value;self.assertIsNone(dl.failure())
     expected=ROOT/f'viewer/public-demo/chair.{ext.lower()}'
     self.assertEqual(hashlib.sha256(Path(dl.path()).read_bytes()).hexdigest(),hashlib.sha256(expected.read_bytes()).hexdigest())
