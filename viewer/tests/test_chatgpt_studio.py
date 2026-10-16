"""Test local ChatGPT handoff and browser-only 3D editing; no external AI calls."""
import json
import os
import shutil
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")

class ChatGPTStudioTests(unittest.TestCase):
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
        context=self.browser.new_context(accept_downloads=True,viewport={"width":1280,"height":900})
        self.addCleanup(context.close)
        page=context.new_page()
        page.goto(URL)
        page.evaluate("document.body.classList.remove('hg-minimal-ui')")
        return page

    def test_manual_prompt_does_not_upload_or_store_files(self):
        page=self.page()
        requests=[]
        page.on("request",lambda req: requests.append(req.url))
        page.locator("#model-instruction").fill("Dựng lại tủ theo mô tả, không tự tạo chi tiết khuất.")
        page.locator("#confirmed-measurements").fill("Rộng 1800 mm, nguồn: yêu cầu chủ nhà")
        page.locator("#cgpt-generate").click()
        text=page.locator("#cgpt-prompt").input_value()
        self.assertIn("1800 mm",text)
        self.assertIn("hg-chatgpt-scene-v1",text)
        self.assertEqual(page.locator("#cgpt-open").get_attribute("href"),"https://chatgpt.com/")
        with page.expect_download() as received:
            page.locator("#cgpt-download-job").click()
        blob=Path(received.value.path()).read_text()
        job=json.loads(blob)
        self.assertFalse(job["image_bytes_included"])
        self.assertEqual(job["mode"],"manual_chatgpt_only")
        self.assertTrue(all(req.startswith(URL) for req in requests))

    def test_pasted_scene_is_editable_and_exports_real_glb(self):
        page=self.page()
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        obj={"schema":"hg-chatgpt-scene-v1","unit":"mm","review_status":"NEEDS_REVIEW",
             "objects":[
                 {"id":"panel","name":"Tấm gỗ","shape":"box","size_mm":[1200,500,25],
                  "position_mm":[0,0,500],"rotation_deg":[0,0,0],"color":"#8a7258"},
                 {"id":"leg","name":"Chân","shape":"box","size_mm":[50,50,450],
                  "position_mm":[-450,0,230],"rotation_deg":[0,0,0],"color":"#555555"}],
             "unknown_details":["Liên kết chân chưa xác minh"]}
        page.locator("#cgpt-scene-json").fill(json.dumps(obj))
        page.locator("#cgpt-preview-json").click()
        page.wait_for_function("() => window.hgChatGPTStudio.ready",timeout=20000)
        self.assertEqual(page.evaluate("hgChatGPTStudio.objects"),2)
        self.assertIn("CẦN XÁC NHẬN",page.locator("#cgpt-result-note").inner_text())
        page.locator("#cgpt-x").fill("150")
        page.locator("#cgpt-scale").fill("125")
        page.locator("#cgpt-apply").click()
        self.assertTrue(page.evaluate("hgChatGPTStudio.edited"))
        with page.expect_download(timeout=20000) as received:
            page.locator("#cgpt-export-glb").click()
        p=Path(received.value.path())
        self.assertEqual(p.read_bytes()[:4],b"glTF")
        self.assertGreater(p.stat().st_size,200)
        self.assertEqual(errors,[])

    def test_missing_dimensions_are_blocked_without_fabricated_mesh(self):
        page=self.page()
        obj={"schema":"hg-chatgpt-scene-v1","unit":"mm","objects":[],"unknown_details":["Chưa có số đo"]}
        page.locator("#cgpt-scene-json").fill(json.dumps(obj))
        page.locator("#cgpt-preview-json").click()
        self.assertIn("Chưa có bộ phận đủ bằng chứng",page.locator("#cgpt-feedback").inner_text())
        self.assertFalse(page.evaluate("hgChatGPTStudio.ready"))
        self.assertTrue(page.locator("#create-job").is_disabled())

if __name__=="__main__":
    unittest.main()
