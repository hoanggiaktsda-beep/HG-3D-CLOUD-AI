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
 assert page.locator('#create-model.hg-launch').is_visible(), 'Single image-first workspace must be displayed'
 assert page.locator('header.hg-topbar').is_hidden(), 'Old navigation must remain hidden'
 assert page.locator('#height').inner_text()=='850'
 assert page.locator('#create-job').is_disabled()
 # Open the preserved viewer explicitly: it is intentionally hidden on the single-screen homepage.
 page.evaluate("location.hash='#sample-viewer'")
 page.wait_for_function("() => window.hgMinimalWorkspace?.mode==='viewer'")
 assert page.locator('.workspace').is_visible()
 page.locator('[data-view=top]').click();assert page.evaluate('hgViewer.currentView')=='top'
 # Public sample downloads are intentionally removed from the default user interface.
 # Verify their live bytes directly without requiring hidden footer links to be clickable.
 for ext in ('glb','blend'):
  response=context.request.get(url+f'assets/sample.{ext}')
  assert response.status==200
  assert response.body()==(root/f'viewer/assets/sample.{ext}').read_bytes()
 # Wait for the ACTIVE controller's public shell to be present before simulating offline.
 # Do not rely only on controller!=null while a new SW/cache install may still be racing.
 page.wait_for_function("""async () => {
   const registration=await navigator.serviceWorker.ready;
   const index=new URL('index.html',registration.scope).href;
   const shell=await caches.match(index);
   return !!navigator.serviceWorker.controller && !!shell && !registration.installing;
 }""",timeout=60000)
 context.set_offline(True);page.reload();page.wait_for_function('()=>hgViewer.ready',timeout=60000)
 assert not errors,errors
 browser.close()
print(json.dumps({'test':32,'url':url,'verified_files':checked,'live_browser':'Chromium Linux, mobile viewport only','downloads':['GLB','BLEND'],'offline_public_viewer':True,'private_ai_worker':'NOT_CONNECTED','test30':'NEEDS_CONFIRMATION','commit':os.environ.get('GITHUB_SHA')},ensure_ascii=False,indent=2))
