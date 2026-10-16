"""No fake AI: test local selection and truthful disconnected behavior."""
import os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get('HG_VIEWER_URL','http://127.0.0.1:8767/HG-3D-CLOUD-AI/')
IMAGE=ROOT/'tests/fixtures/dimensioned_cabinet.png'
class CreateModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(executable_path=__import__('shutil').which('chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.p.stop()
    def page(self,width=1440,height=1000):
        context=self.browser.new_context(viewport={'width':width,'height':height},has_touch=True)
        self.addCleanup(context.close);page=context.new_page();page.goto(URL)
        page.wait_for_function('() => (window.hgViewer?.ready)');return page
    def test_private_selection_never_uploads_or_creates_fake_job(self):
        page=self.page();requests=[]
        page.on('request',lambda r:requests.append((r.method,r.url)) if r.url.startswith(('http://','https://')) else None)
        page.locator('#source-images').set_input_files(IMAGE)
        page.wait_for_function('() => (document.querySelectorAll("#image-previews img").length === 1)')
        self.assertIn('Chưa tải lên máy chủ',page.locator('#image-status').inner_text())
        self.assertEqual(page.locator('#connection-state').inner_text(),'CHƯA KẾT NỐI')
        self.assertTrue(page.locator('#create-job').is_disabled());self.assertTrue(page.locator('#rebuild-job').is_disabled())
        page.locator('#model-instruction').fill('Giữ nguyên sofa, cần xác nhận kích thước khuất')
        page.locator('#confirmed-measurements').fill('Chưa biết chiều sâu')
        self.assertEqual(requests,[])
        self.assertIn('Chưa có công việc',page.locator('#job-state').inner_text())
        self.assertEqual(page.evaluate('localStorage.length'),0)
        self.assertEqual(page.evaluate('sessionStorage.length'),0)
        self.assertEqual(page.locator('.pipeline-steps li').count(),4)
        self.assertEqual(page.locator('#width').inner_text(),'1.800')
        page.locator('#clear-images').click();self.assertEqual(page.locator('#image-previews img').count(),0)
        self.assertEqual(page.locator('#source-images').input_value(),'')
    def test_reject_invalid_and_too_many_files(self):
        page=self.page()
        for filename,mime,content in [('not-an-image.png','image/png',b'bad'),('private.heic','image/heic',b'heic'),('x.svg','image/svg+xml',b'<svg/>'),('forged.png','image/png',b'<svg xmlns="http://www.w3.org/2000/svg"/>')]:
            with self.subTest(filename=filename):
                page.locator('#source-images').set_input_files({'name':filename,'mimeType':mime,'buffer':content})
                page.wait_for_function('() => (document.querySelector("#source-images").value === "")')
                self.assertEqual(page.locator('#image-previews img').count(),0)
        page.locator('#source-images').set_input_files([{'name':str(i)+'.png','mimeType':'image/png','buffer':IMAGE.read_bytes()} for i in range(9)])
        self.assertIn('Tối đa 8 ảnh',page.locator('#image-status').inner_text())
    def test_disconnected_service_rejects_every_job_operation(self):
        page=self.page()
        result=page.evaluate('''async () => {
          const {modelService}=await import('./model-service.js');const errors=[];
          for(const method of ['createJob','getJob','requestRevision','getArtifacts']){
            try{await modelService[method]({privateData:'never sent'});errors.push('UNEXPECTED_SUCCESS');}
            catch(e){errors.push(e.name);}
          }
          return {capabilities:modelService.capabilities(),errors};
        }''')
        self.assertFalse(any(result['capabilities'].values()))
        self.assertEqual(result['errors'],['BackendUnavailableError']*4)
    def test_mobile_tablet_and_desktop_forms(self):
        for width,height in [(390,844),(820,1180),(1440,1000)]:
            with self.subTest(size=(width,height)):
                page=self.page(width,height)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                page.locator('.section-nav a[href="#create-model"]').click()
                page.locator('#input-type').select_option('layout')
                page.locator('#source-images').set_input_files(IMAGE)
                page.wait_for_function('() => (document.querySelectorAll("#image-previews img").length === 1)')
                self.assertEqual(page.locator('#input-type').input_value(),'layout')
                self.assertTrue(page.locator('#create-job').is_disabled())
                page.screenshot(path=str(ROOT/f'outputs/create-model-{width}.png'),full_page=True)
