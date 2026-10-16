"""Browser smoke tests; Chromium emulation is not physical iOS/Safari validation."""
import json,unittest,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get('HG_VIEWER_URL','http://127.0.0.1:8765')

class ViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch(executable_path=__import__('shutil').which('chromium'),headless=True,
          args=['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.p.stop()
    def page(self,**kwargs):
        context=self.browser.new_context(**kwargs);self.addCleanup(context.close)
        return context.new_page()
    def ready(self,page):
        page.goto(URL);page.wait_for_function('() => (window.hgViewer?.ready)',timeout=30000)
        page.evaluate("document.body.classList.remove('hg-minimal-ui')")
    def test_desktop_actual_glb_measurements_and_camera(self):
        page=self.page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        self.ready(page)
        self.assertEqual(page.locator('#mesh-count').inner_text(),'8')
        self.assertEqual(page.locator('#width').inner_text(),'1.800')
        self.assertEqual(page.locator('#depth').inner_text(),'450')
        self.assertEqual(page.locator('#height').inner_text(),'850')
        self.assertEqual(page.locator('#object-rows tr').count(),8)
        for name in ['front','right','top','back','perspective']:
            page.locator(f'[data-view={name}]').click()
            self.assertEqual(page.evaluate('hgViewer.currentView'),name)
            self.assertEqual(page.locator(f'[data-view={name}]').get_attribute('aria-pressed'),'true')
        before=page.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)')
        page.locator('#zoom-in').click();after=page.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)')
        self.assertLess(after,before)
        page.locator('#reset').click()
        canvas=page.locator('canvas').bounding_box();x=canvas['x']+canvas['width']/2;y=canvas['y']+canvas['height']/2
        old=page.evaluate('hgViewer.camera.position.toArray()')
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+120,y+40,steps=8);page.mouse.up()
        self.assertNotEqual(page.evaluate('hgViewer.camera.position.toArray()'),old)
        self.assertEqual(page.evaluate('hgViewer.currentView'),'free')
        self.assertEqual(errors,[])
        page.screenshot(path=str(ROOT/'outputs/viewer-desktop.png'),full_page=True)
    def test_iphone_and_ipad_layout_and_touch(self):
        for width,height in [(390,844),(820,1180),(1180,820)]:
            with self.subTest(size=(width,height)):
                page=self.page(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=2)
                self.ready(page)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                page.locator('[data-view=top]').tap()
                self.assertEqual(page.evaluate('hgViewer.currentView'),'top')
                # Native touch events exercise one finger orbit and two finger pinch.
                canvas=page.locator('canvas').bounding_box();x=canvas['x']+canvas['width']/2;y=canvas['y']+canvas['height']/2
                session=page.context.new_cdp_session(page)
                before=page.evaluate('hgViewer.camera.position.toArray()')
                session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':0}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+60,'y':y+30,'id':0}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                self.assertNotEqual(page.evaluate('hgViewer.camera.position.toArray()'),before)
                before_distance=page.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)')
                session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x-25,'y':y,'id':0},{'x':x+25,'y':y,'id':1}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-60,'y':y,'id':0},{'x':x+60,'y':y,'id':1}]})
                session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                self.assertLess(page.evaluate('hgViewer.camera.position.distanceTo(hgViewer.controls.target)'),before_distance)
                if width==390:page.screenshot(path=str(ROOT/'outputs/viewer-mobile.png'),full_page=True)
    def test_report_cannot_self_approve_or_inject_html(self):
        page=self.page()
        report=json.loads((ROOT/'viewer/assets/sample-qa.json').read_text())
        report['status']='APPROVED';report['unknown_details']=['<img src=x onerror="alert(1)">']
        report['objects'][0]['label']='<script>window.pwned=true</script>'
        page.route('**/assets/sample-qa.json',lambda route:route.fulfill(json=report))
        self.ready(page)
        self.assertIn('CẦN XÁC NHẬN',page.locator('.review-badge').inner_text())
        self.assertEqual(page.locator('#unknown-list img').count(),0)
        self.assertFalse(page.evaluate('Boolean(window.pwned)'))
        self.assertEqual(page.locator('#object-rows td.pending').count(),8)
    def test_missing_glb_shows_error_not_pass(self):
        page=self.page();page.route('**/assets/sample.glb',lambda route:route.fulfill(status=404,body='not found'))
        page.goto(URL);page.evaluate("document.body.classList.remove('hg-minimal-ui')");page.locator('#error').wait_for(state='visible')
        self.assertEqual(page.locator('#qa-result').inner_text(),'CHƯA KIỂM CHỨNG')
        self.assertFalse(page.evaluate('hgViewer.ready'))
    def test_invalid_report_blocks_viewer(self):
        page=self.page();page.route('**/assets/sample-qa.json',lambda route:route.fulfill(json={'status':'APPROVED'}))
        page.goto(URL);page.evaluate("document.body.classList.remove('hg-minimal-ui')");page.locator('#error').wait_for(state='visible')
        self.assertFalse(page.evaluate('hgViewer.ready'))
    def test_no_external_runtime_requests(self):
        page=self.page();external=[]
        page.on('request',lambda request:external.append(request.url) if not request.url.startswith(URL) else None)
        self.ready(page)
        self.assertEqual(external,[])

if __name__=='__main__':unittest.main()
