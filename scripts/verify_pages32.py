"""Verify actual deployed bytes and browser behavior, never fake a deployment."""
import hashlib,json,os
from pathlib import Path
from urllib.request import urlopen,Request
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
url='https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/'
manifest=json.loads((root/'viewer/dist/build-manifest.json').read_text())
checked=[]
for item in manifest['files']:
 with urlopen(Request(url+item['path'],headers={'Cache-Control':'no-cache'}),timeout=60) as response:
  assert response.status==200
  assert hashlib.sha256(response.read()).hexdigest()==item['sha256'],item['path']
 checked.append(item['path'])
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 context=browser.new_context(accept_downloads=True,viewport={'width':390,'height':844})
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(url);page.wait_for_function('()=>window.hgViewer?.ready',timeout=60000)
 assert page.locator('#height').inner_text()=='850'
 assert page.locator('#create-job').is_disabled()
 page.locator('[data-view=top]').click();assert page.evaluate('hgViewer.currentView')=='top'
 for ext in ('glb','blend'):
  with page.expect_download() as event:page.locator(f'a[href="assets/sample.{ext}"]').click()
  dl=event.value;assert dl.failure() is None
  assert Path(dl.path()).read_bytes()==(root/f'viewer/assets/sample.{ext}').read_bytes()
 page.wait_for_function('()=>navigator.serviceWorker.controller!==null',timeout=60000)
 context.set_offline(True);page.reload();page.wait_for_function('()=>hgViewer.ready',timeout=60000)
 assert not errors,errors
 browser.close()
print(json.dumps({'test':32,'url':url,'verified_files':checked,'live_browser':'Chromium Linux, mobile viewport only','downloads':['GLB','BLEND'],'offline_public_viewer':True,'private_ai_worker':'NOT_CONNECTED','test30':'NEEDS_CONFIRMATION','commit':os.environ.get('GITHUB_SHA')},ensure_ascii=False,indent=2))
