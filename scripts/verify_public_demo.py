"""Verify actual published AI-derived bytes, GLB viewer and downloads. No fake models."""
import hashlib,json,os,shutil
from pathlib import Path
from urllib.request import urlopen,Request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('HG_PUBLIC_DEMO_URL','https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/')
release=json.loads((ROOT/'viewer/public-demo/release.json').read_text())
with urlopen(Request(URL+'public-demo/release.json',headers={'Cache-Control':'no-cache'}),timeout=60) as response:
 assert json.load(response)==release,'Published run does not match actual inference'
for f in release['files']:
 with urlopen(Request(URL+f['path'],headers={'Cache-Control':'no-cache'}),timeout=60) as response:
  assert hashlib.sha256(response.read()).hexdigest()==f['sha256'],f['path']
chair=next(c for c in release['cases'] if c['id']=='chair')
assert chair['status']=='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW','No real GLB available; do not claim the complete public demo works'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for width in [390,820,1440]:
  context=browser.new_context(viewport={'width':width,'height':1000},accept_downloads=True)
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(URL+'#public-demo');page.wait_for_function('()=>document.querySelectorAll("#public-demo-cases article").length===3',timeout=60000)
  page.get_by_role('button',name='Xem kết quả AI 3D',exact=True).click();page.wait_for_function('()=>hgPublicDemo.ready',timeout=60000)
  assert page.evaluate('hgPublicDemo.run_id')==release['run_id']
  assert page.evaluate('hgPublicDemo.meshes')==chair['parts']
  assert page.locator('#create-job').is_disabled()
  assert page.evaluate('document.documentElement.scrollWidth')<=width
  for ext in ['GLB','BLEND']:
   with page.expect_download() as event:page.locator('#public-demo-cases').get_by_role('link',name='Tải '+ext,exact=True).click()
   dl=event.value;assert dl.failure() is None
   assert Path(dl.path()).read_bytes()==(ROOT/f'viewer/public-demo/chair.{ext.lower()}').read_bytes()
  assert not errors,errors;context.close()
 browser.close()
summary={'url':URL,'run_id':release['run_id'],'actual_public_ai_result_verified':True,'meshes':chair['parts'],'assembled':False,'customer_upload_connected':False,'browser':'Chromium Linux, emulated widths 390/820/1440; not physical devices'}
print(json.dumps(summary,ensure_ascii=False))
if os.environ.get('GITHUB_ACTIONS'):print('::notice title=Actual public AI website verified::'+json.dumps(summary,ensure_ascii=False))
