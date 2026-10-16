"""Local evidence-gated builder tests: authentic mesh preview and GLB/FBX bytes."""
import os
import shutil
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
IMAGE=ROOT/"tests/fixtures/dimensioned_cabinet.png"

class LocalModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(
            executable_path=shutil.which("chromium"),headless=True,
            args=["--no-sandbox","--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
    def page(self,width=1280,height=850):
        context=self.browser.new_context(accept_downloads=True,viewport={"width":width,"height":height})
        self.addCleanup(context.close)
        page=context.new_page()
        page.goto(URL)
        page.wait_for_function("() => window.hgViewer?.ready",timeout=35000)
        return page
    @staticmethod
    def dimensions(page,w=1800,d=450,h=850):
        page.locator("#hg-width").fill(str(w))
        page.locator("#hg-depth").fill(str(d))
        page.locator("#hg-height").fill(str(h))
        page.locator("#hg-confirm-dims").check()
    def test_verified_photo_without_measurements_must_not_invent_3d(self):
        page=self.page()
        page.locator("#source-images").set_input_files(IMAGE)
        page.wait_for_function("() => window.hgLocalModules.imageCount === 1",timeout=12000)
        page.locator("#hg-run-modules").click()
        self.assertEqual(page.evaluate("window.hgLocalModules.runs"),0)
        self.assertEqual(page.evaluate("window.hgLocalModules.status"),"WAITING_CHATGPT_IMAGE_ANALYSIS")
        self.assertIn("chưa được AI phân tích",page.locator("#hg-engine-result").inner_text())
        self.assertEqual(page.locator("#mesh-count").inner_text(),"—")
        self.assertTrue(page.locator("#hg-download-fbx").is_hidden())

    def test_dimensions_enable_real_3d_in_original_main_viewer(self):
        page=self.page()
        self.dimensions(page)
        page.wait_for_function("() => window.hgLocalModules.runs >= 1",timeout=15000)
        self.assertEqual(page.evaluate("window.hgLocalModules.status"),"BUILT_PARAMETRIC_DRAFT")
        self.assertEqual(page.evaluate("window.hgViewer.displayMode"),"local_draft")
        self.assertEqual(page.locator("#mesh-count").inner_text(),"1")
        self.assertEqual(page.locator("#width").inner_text(),"1.800")
        self.assertEqual(page.locator("#depth").inner_text(),"450")
        self.assertEqual(page.locator("#height").inner_text(),"850")
        self.assertIn("CẦN XÁC NHẬN",page.locator("#qa-result").inner_text())
        self.assertTrue(page.locator("#hg-download-glb").is_visible())
        self.assertTrue(page.locator("#hg-download-fbx").is_visible())
        page.locator("#hg-template").select_option("console")
        page.wait_for_function("() => window.hgLocalModules.runs >= 2",timeout=15000)
        self.assertGreater(page.evaluate("window.hgViewer.localMeshes"),5)
        self.assertIn("cấu tạo minh họa",page.locator("#hg-mod-qa").inner_text()+" "+page.locator("#hg-engine-result").inner_text()+" "+page.locator("#cgpt-result-note").inner_text()+" "+page.locator("#cgpt-scene-json").input_value())
    def test_real_binary_fbx_and_glb_download_and_fbx_loader(self):
        page=self.page()
        self.dimensions(page)
        page.wait_for_function("() => window.hgLocalModules.runs >= 1",timeout=15000)
        with page.expect_download(timeout=40000) as received:
            page.locator("#hg-download-fbx").click()
        fbx=Path(received.value.path()).read_bytes()
        self.assertTrue(fbx.startswith(b"Kaydara FBX Binary"))
        self.assertGreater(len(fbx),500)
        # Use three.js FBXLoader to parse actual bytes, not just the file header.
        page.route("**/fbx-import-probe",lambda route:route.fulfill(body=fbx,content_type="application/octet-stream"))
        result=page.evaluate("""async () => {
          const { FBXLoader }=await import('three/addons/loaders/FBXLoader.js');
          const response=await fetch('./fbx-import-probe');
          const bytes=await response.arrayBuffer();
          const root=new FBXLoader().parse(bytes,'');
          const meshes=[];root.traverse(o=>{if(o.isMesh)meshes.push(o);});
          return {count:meshes.length,bounding:meshes[0]?.geometry?.attributes?.position?.count||0};
        }""")
        self.assertGreaterEqual(result["count"],1)
        self.assertGreater(result["bounding"],0)
        with page.expect_download(timeout=30000) as received:
            page.locator("#hg-download-glb").click()
        glb=Path(received.value.path()).read_bytes()
        self.assertEqual(glb[:4],b"glTF")
        self.assertGreater(len(glb),200)
    def test_auto_rerun_after_verified_upload_with_confirmed_dimensions(self):
        page=self.page()
        self.dimensions(page)
        page.wait_for_function("() => window.hgLocalModules.runs >= 1",timeout=12000)
        before=page.evaluate("hgLocalModules.runs")
        page.locator("#source-images").set_input_files(IMAGE)
        page.wait_for_function("() => window.hgLocalModules.imageCount === 1 && window.hgLocalModules.status === 'WAITING_CHATGPT_IMAGE_ANALYSIS'",timeout=15000)
        self.assertEqual(page.evaluate("hgLocalModules.runs"),before)
        self.assertEqual(page.evaluate("hgViewer.displayMode"),"awaiting_photo_analysis")
        self.assertIn("Đã xác minh 1 ảnh",page.locator("#hg-mod-source").inner_text())
        page.locator("#hg-allow-illustration").check()
        page.wait_for_function("(n) => window.hgLocalModules.runs > n",arg=before,timeout=15000)
        self.assertEqual(page.evaluate("hgLocalModules.status"),"BUILT_PARAMETRIC_DRAFT")
        self.assertEqual(page.evaluate("localStorage.length"),0)
        self.assertEqual(page.evaluate("sessionStorage.length"),0)

if __name__=="__main__":
    unittest.main()
