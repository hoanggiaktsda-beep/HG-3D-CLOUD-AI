"""Verify that the image-first 3D workspace is operational, not only a visual imitation."""
import os
import shutil
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
SOURCE=ROOT/"tests/fixtures/dimensioned_cabinet.png"

class WorkspaceLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(
            executable_path=shutil.which("chromium"),headless=True,
            args=["--no-sandbox","--enable-webgl","--use-gl=angle",
                  "--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
    def page(self, width=1380, height=900):
        ctx=self.browser.new_context(viewport={"width":width,"height":height},
                                     accept_downloads=True,permissions=["clipboard-read","clipboard-write"])
        self.addCleanup(ctx.close)
        page=ctx.new_page()
        page.goto(URL)
        page.wait_for_function("() => window.hgViewer?.ready && !!window.hgWorkspaceLauncher && !!window.hgPhotoHandoff",timeout=35000)
        return page

    def test_upload_hero_real_photo_verification_and_handoff(self):
        page=self.page()
        page.locator("#hg-launch").wait_for(state="visible")
        self.assertTrue(page.locator("#hg-upload-drop").is_visible())
        self.assertTrue(page.locator("#hg-launch-analyze").is_disabled())
        with page.expect_file_chooser() as chooser:
            page.locator("#hg-upload-drop").click()
        chooser.value.set_files(SOURCE)
        page.wait_for_function("() => hgWorkspaceLauncher.verified === 1 && hgPhotoHandoff.verifiedImages === 1",timeout=15000)
        self.assertTrue(page.locator("#hg-upload-loaded").is_visible())
        self.assertTrue(page.locator("#hg-launch-analyze").is_enabled())
        self.assertIn("Đã nhận 1 ảnh",page.locator("#hg-stage-source").inner_text())
        self.assertEqual(page.evaluate("hgViewer.displayMode"),"awaiting_photo_analysis")
        self.assertEqual(page.evaluate("hgLocalModules.runs"),0)
        self.assertTrue(page.locator("#hg-download-glb").is_hidden())
        self.assertEqual(page.evaluate("localStorage.length"),0)

    def test_editable_parts_choice_changes_real_chatgpt_prompt(self):
        page=self.page()
        page.locator("#source-images").set_input_files(SOURCE)
        page.wait_for_function("() => hgWorkspaceLauncher.verified === 1",timeout=15000)
        page.locator('input[name="hg-model-priority"][value="parts"]').check()
        page.locator("#hg-launch-analyze").click()
        page.wait_for_function("() => !!document.querySelector('#cgpt-prompt').value",timeout=10000)
        content=page.locator("#cgpt-prompt").input_value()
        self.assertIn("Ưu tiên tách các phần quan sát",content)
        self.assertEqual(page.evaluate("hgPhotoHandoff.prepared"),True)
        self.assertIn("Lệnh đã chuẩn bị",page.locator("#hg-stage-analysis").inner_text())
        self.assertIn("BẮT BUỘC NHẬN DIỆN ĐÚNG ẢNH",content)
        self.assertEqual(page.evaluate("hgChatGPTStudio.ready"),False)

    def test_drag_drop_files_and_source_clear(self):
        page=self.page()
        # Browser-local File in DragEvent; no external upload or URL involved.
        encoded=__import__("base64").b64encode(SOURCE.read_bytes()).decode("ascii")
        page.evaluate("""base64 => {
          const binary=atob(base64);
          const bytes=new Uint8Array(binary.length);
          for(let i=0;i<binary.length;i++) bytes[i]=binary.charCodeAt(i);
          const file=new File([bytes],'private-photo.png',{type:'image/png'});
          const dt=new DataTransfer();dt.items.add(file);
          const root=document.querySelector('#hg-upload-drop');
          root.dispatchEvent(new DragEvent('dragenter',{bubbles:true,cancelable:true,dataTransfer:dt}));
          root.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));
        }""",encoded)
        page.wait_for_function("() => hgWorkspaceLauncher.verified===1",timeout=15000)
        self.assertEqual(page.locator("#source-images").evaluate("(el)=>el.files[0].name"),"private-photo.png")
        page.locator("#clear-images").click()
        page.wait_for_function("() => hgWorkspaceLauncher.verified===0",timeout=15000)
        self.assertTrue(page.locator("#hg-upload-empty").is_visible())
        self.assertTrue(page.locator("#hg-launch-analyze").is_disabled())

    def test_mobile_hero_has_no_horizontal_overflow(self):
        for width,height in [(320,640),(390,844),(820,1180)]:
            with self.subTest(viewport=width):
                page=self.page(width,height)
                self.assertTrue(page.locator("#hg-upload-drop").is_visible())
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width+1)
                self.assertTrue(page.locator(".hg-inspector-steps").is_visible())

if __name__=="__main__":unittest.main()
