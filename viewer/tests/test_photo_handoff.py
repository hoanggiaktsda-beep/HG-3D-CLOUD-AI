"""Photograph handling must never hallucinate a generic four-legged table."""
import json
import os
import shutil
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
SOURCE=ROOT/"tests/fixtures/dimensioned_cabinet.png"

class PhotoHandoffTests(unittest.TestCase):
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
    def page(self):
        ctx=self.browser.new_context(viewport={"width":1280,"height":850},
                                     accept_downloads=True, permissions=["clipboard-read","clipboard-write"])
        self.addCleanup(ctx.close)
        page=ctx.new_page()
        page.goto(URL)
        page.wait_for_function("() => window.hgViewer?.ready && !!window.hgPhotoHandoff",timeout=35000)
        return page

    def test_upload_removes_old_model_and_does_not_assume_a_table(self):
        page=self.page()
        page.locator("#hg-width").fill("1800")
        page.locator("#hg-depth").fill("450")
        page.locator("#hg-height").fill("850")
        page.locator("#hg-template").select_option("table")
        page.locator("#hg-confirm-dims").check()
        page.wait_for_function("() => hgLocalModules.runs > 0")
        self.assertEqual(page.evaluate("hgViewer.localMeshes"),5)
        page.locator("#source-images").set_input_files(SOURCE)
        page.wait_for_function("() => hgPhotoHandoff.verifiedImages === 1 && hgLocalModules.status === 'WAITING_CHATGPT_IMAGE_ANALYSIS'",timeout=18000)
        self.assertFalse(page.locator("#hg-allow-illustration").is_checked())
        self.assertEqual(page.evaluate("hgViewer.displayMode"),"awaiting_photo_analysis")
        self.assertIn("CHỜ PHÂN TÍCH ẢNH",page.locator("#sample-viewer h1").inner_text())
        self.assertIn("ĐÃ NHẬN ẢNH · CHƯA NHẬN DIỆN",page.locator("#hg-photo-analysis-state").inner_text())
        self.assertEqual(page.locator("#mesh-count").inner_text(),"—")
        self.assertTrue(page.locator("#hg-photo-reference").is_visible())
        self.assertTrue(page.locator("#hg-download-fbx").is_hidden())
        page.locator("#hg-run-modules").click()
        self.assertEqual(page.evaluate("hgViewer.displayMode"),"awaiting_photo_analysis")
        self.assertEqual(page.evaluate("hgChatGPTStudio.ready"),False)
        self.assertEqual(page.evaluate("localStorage.length"),0)

    def test_photo_prompt_is_image_grounded_not_four_legs_default(self):
        page=self.page()
        page.locator("#source-images").set_input_files(SOURCE)
        page.wait_for_function("() => hgPhotoHandoff.verifiedImages === 1",timeout=12000)
        page.locator("#model-instruction").fill("Dựng mẫu bàn trà thấp có hốc lõm ở giữa nếu ảnh cho thấy như vậy.")
        page.locator("#hg-photo-copy-prompt").click()
        prompt=page.locator("#cgpt-prompt").input_value()
        self.assertIn("BẮT BUỘC NHẬN DIỆN ĐÚNG ẢNH",prompt)
        self.assertIn("không thay ảnh bàn trà khối hộp",prompt.lower())
        self.assertIn("các tấm viền",prompt)
        self.assertEqual(page.locator("#hg-photo-open-chatgpt").get_attribute("href"),"https://chatgpt.com/")
        self.assertEqual(page.evaluate("hgPhotoHandoff.prepared"),True)
        self.assertEqual(page.evaluate("hgPhotoHandoff.imported"),False)
        self.assertEqual(page.evaluate("hgLocalModules.runs"),0)

    def test_user_supplied_recessed_shape_json_builds_without_template(self):
        page=self.page()
        page.locator("#source-images").set_input_files(SOURCE)
        page.wait_for_function("() => hgPhotoHandoff.verifiedImages === 1",timeout=12000)
        parts=[
          ("front",[1100,85,240],[0,-360,130]),
          ("back",[1100,85,240],[0,360,130]),
          ("left",[85,635,240],[-507.5,0,130]),
          ("right",[85,635,240],[507.5,0,130]),
          ("basin",[930,635,35],[0,0,38]),
          ("base",[1000,690,45],[0,0,22.5])
        ]
        scene={"schema":"hg-chatgpt-scene-v1","unit":"mm","review_status":"NEEDS_REVIEW",
               "objects":[{"id":ident,"name":ident,"shape":"box","size_mm":dims,"position_mm":pos,
                           "rotation_deg":[0,0,0],"color":"#685b4e","confidence":"inferred"}
                          for ident,dims,pos in parts],
               "unknown_details":["Vật liệu, chiều sâu lõm và cấu tạo còn cần đo thực tế"]}
        page.locator("#cgpt-scene-json").fill(json.dumps(scene))
        page.locator("#cgpt-preview-json").click()
        page.wait_for_function("() => hgPhotoHandoff.imported && hgViewer.displayMode === 'local_draft'",timeout=15000)
        self.assertEqual(page.evaluate("hgChatGPTStudio.objects"),6)
        self.assertEqual(page.evaluate("hgLocalModules.runs"),0)
        self.assertIn("CẦN ĐỐI CHIẾU",page.locator("#hg-photo-reference-status").inner_text())
        self.assertIn("CẦN XÁC NHẬN",page.locator("#cgpt-result-note").inner_text())
        self.assertTrue(page.locator("#hg-download-glb").is_visible())
        with page.expect_download() as downloaded:
            page.locator("#hg-download-glb").click()
        self.assertEqual(Path(downloaded.value.path()).read_bytes()[:4],b"glTF")

if __name__=="__main__":
    unittest.main()
