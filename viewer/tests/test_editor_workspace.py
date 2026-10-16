"""End-to-end 3D AI editing workspace: real mesh engine, parts, material and binary exports."""
import json, os, shutil, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

URL=os.environ.get("HG_VIEWER_URL","http://127.0.0.1:8765")
SCENE={
 "schema":"hg-chatgpt-scene-v1","unit":"mm","review_status":"NEEDS_REVIEW",
 "objects":[
  {"id":"top","name":"Mặt trên","shape":"box","size_mm":[1500,500,32],
   "position_mm":[0,0,710],"rotation_deg":[0,0,0],"color":"#a38a72"},
  {"id":"leg","name":"Chân phải","shape":"box","size_mm":[80,80,690],
   "position_mm":[650,0,345],"rotation_deg":[0,0,0],"color":"#4a544c"}],
 "unknown_details":["Độ dày, khớp lắp và vật liệu thật cần kiểm tra"]
}
class EditorWorkspaceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start()
  cls.browser=cls.p.chromium.launch(executable_path=shutil.which("chromium"),headless=True,
   args=["--no-sandbox","--enable-webgl","--use-gl=angle",
         "--use-angle=swiftshader","--enable-unsafe-swiftshader"])
 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.p.stop()
 def page(self,width=1440,height=900):
  c=self.browser.new_context(viewport={"width":width,"height":height},accept_downloads=True)
  self.addCleanup(c.close)
  p=c.new_page()
  self.errors=[]
  p.on("pageerror",lambda err:self.errors.append(str(err)))
  p.goto(URL+"#chatgpt-studio")
  p.wait_for_function("() => hgMinimalWorkspace?.mode==='editor' && !!window.hgEditorWorkspace && !!window.hgChatGPTStudio && !!window.hgViewer?.ready",timeout=35000)
  return p
 def load(self,p):
  p.locator("#cgpt-scene-json").fill(json.dumps(SCENE))
  p.locator("#cgpt-preview-json").click()
  p.wait_for_function("() => hgChatGPTStudio.ready && hgChatGPTStudio.objects===2",timeout=15000)
  self.assertEqual(p.evaluate("hgViewer.displayMode"),"local_draft")

 def test_five_zone_editor_is_real_and_blank_model_cannot_export(self):
  p=self.page()
  self.assertTrue(p.locator("#hg-ws-import-glb").is_visible())
  self.assertTrue(p.locator(".hg-ws-rail").is_visible())
  self.assertTrue(p.locator(".cgpt-grid").is_visible())
  self.assertTrue(p.locator("#cgpt-viewport").is_visible())
  self.assertTrue(p.locator(".cgpt-inspector").is_visible())
  self.assertTrue(p.locator("#hg-ws-top-glb").is_disabled())
  self.assertTrue(p.locator("#hg-ws-top-fbx").is_disabled())
  self.assertEqual(p.evaluate("hgEditorWorkspace.tool"),"model")
  self.assertIn("Chưa có mô hình",p.locator("#hg-ws-project-state").inner_text())
  self.assertGreater(p.locator("#cgpt-viewport").bounding_box()["height"],240)
  self.assertEqual(p.locator("body").get_attribute("class").count("hg-show-editor"),1)
  self.assertTrue(p.locator(".hg-side").is_hidden())
  self.assertEqual(self.errors,[])

 def test_generate_real_parametric_model_inside_workshop_and_export(self):
  p=self.page()
  p.locator("#hg-ws-create-template").select_option("open_tray")
  p.locator("#hg-ws-create-width").fill("920")
  p.locator("#hg-ws-create-depth").fill("470")
  p.locator("#hg-ws-create-height").fill("750")
  p.locator("#hg-ws-create-model").click()
  self.assertIn("xác nhận",p.locator("#hg-ws-create-result").inner_text().lower())
  self.assertFalse(p.evaluate("hgChatGPTStudio.ready"))
  p.locator("#hg-ws-create-confirm").check()
  p.locator("#hg-ws-create-model").click()
  p.wait_for_function("() => hgLocalModules.status==='BUILT_PARAMETRIC_DRAFT' && hgChatGPTStudio.ready",timeout=15000)
  self.assertEqual(p.evaluate("hgChatGPTStudio.objects"),9)
  self.assertEqual(p.locator("#hg-ws-asset-count").inner_text(),"9")
  self.assertIn("mẫu minh họa",p.locator("#hg-ws-create-result").inner_text().lower())
  self.assertIn("NEEDS_REVIEW",p.locator("#cgpt-scene-json").input_value())
  data=json.loads(p.locator("#cgpt-scene-json").input_value())
  self.assertFalse(any(part["id"]=="top" for part in data["objects"]))
  self.assertEqual(len([part for part in data["objects"] if part["id"].startswith("tray_leg_")]),4)
  with p.expect_download(timeout=40000) as received:
   p.locator("#hg-ws-top-glb").click()
  self.assertEqual(Path(received.value.path()).read_bytes()[:4],b"glTF")
  with p.expect_download(timeout=40000) as received:
   p.locator("#hg-ws-top-fbx").click()
  self.assertTrue(Path(received.value.path()).read_bytes().startswith(b"Kaydara FBX Binary"))
  self.assertEqual(self.errors,[])

 def test_triposr_local_explicit_consent_and_mocked_glb_import(self):
  # This test mocks the local TripoSR HTTP response with a fixture.
  # It does NOT prove the TripoSR model or GPU has run.
  p=self.page(390,844)
  self.assertTrue(p.locator("#hg-triposr-generate").is_disabled())
  self.assertIn("CHƯA KẾT NỐI",p.locator("#hg-triposr-status").inner_text())
  hits=[]
  sample=(Path(__file__).resolve().parents[1]/"assets/sample.glb").read_bytes()
  def route_bridge(route):
   request=route.request
   hits.append((request.method,request.url))
   headers={"Access-Control-Allow-Origin":URL.split("/HG-3D-CLOUD-AI/")[0],
            "Access-Control-Allow-Private-Network":"true",
            "Access-Control-Allow-Headers":"Content-Type",
            "Access-Control-Allow-Methods":"GET,POST,OPTIONS"}
   if request.method=="OPTIONS":
    route.fulfill(status=204,headers=headers)
   elif request.url.endswith("/health"):
    route.fulfill(status=200,headers=headers,content_type="application/json",
      body=json.dumps({"engine":"TripoSR","local_only":True,"engine_found":True,"inference_verified":False}))
   else:
    route.fulfill(status=200,headers=headers,content_type="model/gltf-binary",body=sample)
  p.route("http://127.0.0.1:8787/**",route_bridge)
  self.assertEqual(hits,[])
  photo=Path(__file__).resolve().parents[2]/"tests/fixtures/dimensioned_cabinet.png"
  p.locator("#source-images").set_input_files(photo)
  p.wait_for_function("() => hgPhotoHandoff.verifiedImages===1")
  self.assertTrue(p.locator("#hg-triposr-generate").is_disabled())
  self.assertEqual(hits,[])
  p.locator("#hg-triposr-check").click()
  p.wait_for_function("() => hgTripoSRLocal.connected===true")
  self.assertTrue(p.locator("#hg-triposr-generate").is_disabled())
  p.locator("#hg-triposr-consent").check()
  self.assertTrue(p.locator("#hg-triposr-generate").is_enabled())
  p.locator("#hg-triposr-generate").click()
  p.wait_for_function("() => hgChatGPTStudio.ready && hgTripoSRLocal.working===false",timeout=30000)
  self.assertTrue(p.locator("#hg-ws-top-glb").is_enabled())
  self.assertIn("TripoSR",p.locator("#hg-ws-project-name").inner_text())
  self.assertIn("cần kiểm định",p.locator("#hg-triposr-status").inner_text())
  self.assertTrue(any("/v1/generate" in url and method=="POST" for method,url in hits))
  self.assertEqual(self.errors,[])

 def test_image_never_auto_generates_wrong_product_without_explicit_consent(self):
  p=self.page()
  photo=Path(__file__).resolve().parents[2]/"tests/fixtures/dimensioned_cabinet.png"
  p.locator("#source-images").set_input_files(photo)
  p.wait_for_function("() => hgPhotoHandoff.verifiedImages===1",timeout=15000)
  p.locator("#hg-ws-create-template").select_option("open_tray")
  p.locator("#hg-ws-create-width").fill("920")
  p.locator("#hg-ws-create-depth").fill("470")
  p.locator("#hg-ws-create-height").fill("750")
  p.locator("#hg-ws-create-confirm").check()
  self.assertTrue(p.locator("#hg-ws-create-illustration-wrap").is_visible())
  p.locator("#hg-ws-create-model").click()
  self.assertIn("không theo ảnh",p.locator("#hg-ws-create-result").inner_text().lower())
  self.assertFalse(p.evaluate("hgChatGPTStudio.ready"))
  p.locator("#hg-ws-create-illustration").check()
  p.locator("#hg-ws-create-model").click()
  p.wait_for_function("() => hgLocalModules.status==='BUILT_PARAMETRIC_DRAFT' && hgChatGPTStudio.ready",timeout=15000)
  self.assertEqual(p.evaluate("hgChatGPTStudio.objects"),9)
  self.assertEqual(p.evaluate("localStorage.length"),0)
  self.assertEqual(self.errors,[])

 def test_model_brief_reuses_existing_chatgpt_prompt_generator(self):
  p=self.page()
  p.locator("#hg-ws-instruction").fill("Sofa hai chỗ có console giữa và hai tựa lưng độc lập.")
  p.locator("#hg-ws-measurements").fill("Dài 2460 mm, sâu 1100 mm, cao 770 mm - nguồn hãng")
  p.locator("#hg-ws-input-kind").select_option("product_photo")
  self.assertIn("console giữa",p.locator("#model-instruction").input_value())
  p.locator("#cgpt-generate").click()
  prompt=p.locator("#cgpt-prompt").input_value()
  self.assertIn("2460 mm",prompt)
  self.assertIn("Sofa hai chỗ",prompt)
  self.assertIn("ảnh tôi đính kèm",prompt.lower())
  self.assertEqual(p.evaluate("hgChatGPTStudio.ready"),False)
  self.assertEqual(p.evaluate("localStorage.length"),0)
  self.assertEqual(self.errors,[])

 def test_parts_properties_material_and_real_binary_exports(self):
  p=self.page()
  self.load(p)
  self.assertTrue(p.locator("#hg-ws-top-glb").is_enabled())
  self.assertEqual(p.locator("#hg-ws-asset-count").inner_text(),"2")
  p.locator('[data-ws-tool="parts"]').click()
  self.assertTrue(p.locator("#hg-ws-assets-panel").is_visible())
  self.assertEqual(p.locator("#hg-ws-mesh-assets button").count(),2)
  p.locator("#hg-ws-mesh-assets button").nth(1).click()
  self.assertEqual(p.locator("#hg-ws-part-name").input_value(),"Chân phải")
  p.locator("#hg-ws-part-name").fill("Chân inox")
  p.locator("#hg-ws-part-color").fill("#ccb77a")
  p.locator("#hg-ws-part-visible").uncheck()
  p.locator("#hg-ws-apply-appearance").click()
  sel=p.evaluate("hgChatGPTStudio.getSelectedPart()")
  self.assertEqual(sel["name"],"Chân inox")
  self.assertFalse(sel["visible"])
  self.assertEqual(sel["color"].lower(),"#ccb77a")
  p.locator("#cgpt-x").fill("620")
  p.locator("#cgpt-apply").click()
  self.assertTrue(p.evaluate("hgChatGPTStudio.edited"))
  p.locator('[data-ws-tool="material"]').click()
  p.locator("#hg-ws-grid").uncheck()
  p.locator("#hg-ws-wireframe").check()
  self.assertTrue(p.locator("#hg-ws-wireframe").is_checked())
  p.locator('[data-ws-view="front"]').click()
  self.assertEqual(p.evaluate("hgChatGPTStudio.currentView"),"front")
  p.locator('[data-ws-tool="export"]').click()
  self.assertTrue(p.locator("#hg-ws-panel-glb").is_visible())
  with p.expect_download(timeout=40000) as received:
   p.locator("#hg-ws-panel-glb").click()
  glb=Path(received.value.path()).read_bytes()
  self.assertEqual(glb[:4],b"glTF")
  self.assertGreater(len(glb),300)
  with p.expect_download(timeout=40000) as received:
   p.locator("#hg-ws-top-fbx").click()
  fbx=Path(received.value.path()).read_bytes()
  self.assertTrue(fbx.startswith(b"Kaydara FBX Binary"))
  self.assertGreater(len(fbx),500)
  self.assertEqual(self.errors,[])

 def test_iphone_contextual_panels_and_touch_layout(self):
  for width,height in [(320,640),(375,812),(390,844),(430,932)]:
   with self.subTest(width=width):
    p=self.page(width,height)
    self.assertTrue(p.locator(".cgpt-grid").is_visible())
    self.assertTrue(p.locator(".cgpt-inspector").is_hidden())
    self.assertGreaterEqual(p.locator("#cgpt-viewport").bounding_box()["height"],150)
    self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"),width+1)
    p.locator('[data-ws-tool="parts"]').click()
    self.assertTrue(p.locator(".cgpt-inspector").is_visible())
    self.assertTrue(p.locator(".cgpt-grid").is_hidden())
    self.assertTrue(p.locator("#hg-ws-assets-panel").is_visible())
    p.locator("#hg-ws-properties-tab").click()
    self.assertTrue(p.locator("#hg-ws-properties-panel").is_visible())
    p.locator('[data-ws-tool="material"]').click()
    self.assertTrue(p.locator(".cgpt-grid").is_visible())
    self.assertTrue(p.locator(".cgpt-inspector").is_hidden())
    p.locator('[data-ws-tool="export"]').click()
    self.assertTrue(p.locator("#hg-ws-panel-glb").is_visible())
    self.assertEqual(self.errors,[])

 def test_mobile_and_tablet_workbench_remain_accessible(self):
  for width,height in [(320,640),(390,844),(820,1180),(1200,800)]:
   with self.subTest(width=width):
    p=self.page(width,height)
    self.assertTrue(p.locator(".hg-ws-rail").is_visible())
    self.assertTrue(p.locator("#cgpt-viewport").is_visible())
    self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"),width+1)
    self.assertTrue(p.locator(".hg-ws-back").is_visible())
    self.assertTrue(p.locator('[data-ws-tool="material"]').is_visible())
    self.assertEqual(self.errors,[])

if __name__=="__main__":unittest.main()
