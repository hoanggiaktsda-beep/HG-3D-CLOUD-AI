"""Ensure only the approved image-to-3D launcher is visible by default."""
import os, shutil, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
PHOTO=Path(__file__).resolve().parents[2]/"tests/fixtures/dimensioned_cabinet.png"
class OneScreenTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start()
  cls.browser=cls.p.chromium.launch(executable_path=shutil.which("chromium"),headless=True,args=["--no-sandbox","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def page(self,w=1400,h=900):
  c=self.browser.new_context(viewport={"width":w,"height":h},accept_downloads=True)
  self.addCleanup(c.close)
  p=c.new_page();p.goto(URL+"#create-model")
  p.wait_for_function("() => hgViewer?.ready && !!window.hgMinimalWorkspace")
  return p
 def test_only_hero_visible(self):
  p=self.page()
  self.assertTrue(p.locator("#create-model.hg-launch").is_visible())
  self.assertEqual(p.locator("main.hg-content > section:visible").count(),1)
  for selector in [".hg-side","header.hg-topbar",".hg-mobile-nav",".hg-stats",".section-nav","#sample-viewer",".workspace",".objects-section","#public-demo","#create-details",".app-section","footer"]:
   self.assertTrue(p.locator(selector).is_hidden(),selector)
  self.assertEqual(p.evaluate("hgMinimalWorkspace.mode"),"launch")
  for name in ["hgViewer","hgChatGPTStudio","hgPhotoHandoff","hgLocalModules","hgWorkspaceLauncher"]:
   self.assertTrue(p.evaluate("!!window."+name),name)
 def test_photo_prompt_and_editor_are_on_demand(self):
  p=self.page()
  p.locator("#source-images").set_input_files(PHOTO)
  p.wait_for_function("() => hgWorkspaceLauncher.verified === 1")
  p.locator("#hg-launch-analyze").click()
  self.assertTrue(p.locator("#hg-minimal-prompt-panel").is_visible())
  self.assertIn("BẮT BUỘC NHẬN DIỆN ĐÚNG ẢNH",p.locator("#hg-minimal-prompt").input_value())
  p.locator(".hg-launch-outline[href='#chatgpt-studio']").click()
  p.wait_for_function("() => hgMinimalWorkspace.mode === 'editor'")
  self.assertTrue(p.locator("#chatgpt-studio").is_visible())
  self.assertTrue(p.locator("#create-model").is_hidden())
  p.locator(".hg-ws-back[href='#create-model']").click()
  p.wait_for_function("() => hgMinimalWorkspace.mode === 'launch'")
  self.assertTrue(p.locator("#create-model").is_visible())
  self.assertTrue(p.locator("#chatgpt-studio").is_hidden())
 def test_no_sample_model_masquerading_as_photo(self):
  p=self.page()
  p.locator(".hg-inspector-steps a[href='#sample-viewer']").click()
  self.assertEqual(p.evaluate("hgMinimalWorkspace.mode"),"launch")
  self.assertIn("Chưa có mô hình",p.locator("#hg-launch-upload-status").inner_text())
 def test_mobile_viewport(self):
  for w,h in [(320,640),(390,844),(820,1180),(1440,900)]:
   with self.subTest(width=w):
    p=self.page(w,h)
    self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"),w+1)
    self.assertTrue(p.locator("#hg-upload-drop").is_visible())
    self.assertTrue(p.locator("header.hg-topbar").is_hidden())
if __name__=="__main__":unittest.main()
