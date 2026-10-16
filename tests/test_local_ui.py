"""Real browser -> loopback API -> SQLite -> Blender -> private GLB display."""
import json,secrets,subprocess,sys,tempfile,time,unittest,hashlib
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class LocalUITests(unittest.TestCase):
    def test_real_browser_pipeline_and_no_public_secret(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.private',prefix='ui-test-') as td:
            root=Path(td);creds={'alice':secrets.token_urlsafe(40),'bob':secrets.token_urlsafe(40)}
            credentials=root/'credentials.json';credentials.write_text(json.dumps(creds));storage=root/'jobs'
            process=subprocess.Popen([sys.executable,'scripts/backend.py','api','--root',str(storage),'--credentials',str(credentials),'--port','8773'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.addCleanup(lambda:process.poll() is None and process.terminate())
            try:
                for _ in range(60):
                    try:
                        if httpx.get('http://127.0.0.1:8773/local/').status_code==200:break
                    except httpx.TransportError:time.sleep(.1)
                else:self.fail('Local UI server did not start')
                with sync_playwright() as p:
                    browser=p.chromium.launch(executable_path=__import__('shutil').which('chromium'),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
                    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto('http://127.0.0.1:8773/local/');page.locator('#local-token').wait_for()
                    # Wrong token cannot enable job submission.
                    page.locator('#local-token').fill('bad');page.locator('#local-login').click()
                    page.wait_for_function('() => (document.querySelector("#local-status").textContent.includes("Chưa xác thực"))')
                    self.assertTrue(page.locator('#create-job').is_disabled())
                    page.locator('#local-token').fill(creds['alice']);page.locator('#local-login').click()
                    page.wait_for_function('() => (!document.querySelector("#create-job").disabled)')
                    self.assertEqual(page.locator('#local-token').input_value(),'')
                    self.assertEqual(page.evaluate('localStorage.length+sessionStorage.length'),0)
                    self.assertNotIn(creds['alice'],page.content())
                    page.locator('#source-images').set_input_files(ROOT/'tests/fixtures/dimensioned_cabinet.png')
                    page.locator('#model-instruction').fill('Dựng từ số đo đã xác minh, không render')
                    page.locator('#create-job').click()
                    page.wait_for_function('() => (document.querySelector("#job-state").textContent.includes("WAITING_ANALYSIS"))')
                    owner={'Authorization':'Bearer '+creds['alice']};other={'Authorization':'Bearer '+creds['bob']}
                    jobs=httpx.get('http://127.0.0.1:8773/jobs',headers=owner).json();jid=jobs[0]['id']
                    self.assertEqual(httpx.get(f'http://127.0.0.1:8773/jobs/{jid}',headers=other).status_code,404)
                    self.assertEqual(httpx.get(f'http://127.0.0.1:8773/jobs/{jid}/artifacts/glb').status_code,401)
                    self.assertEqual(httpx.get('http://127.0.0.1:8773/jobs',headers=owner|{'Host':'attacker.example'}).status_code,403)
                    obs=ROOT/'tests/fixtures/cabinet_observations.json'
                    page.locator('#verified-observations').set_input_files(obs);page.locator('#reviewed-check').check()
                    page.locator('#submit-observations').click()
                    page.wait_for_function('() => (document.querySelector("#job-state").textContent.includes("QUEUED"))')
                    result=subprocess.run([sys.executable,'scripts/backend.py','worker','--root',str(storage),'--once'],cwd=ROOT,capture_output=True,timeout=180)
                    self.assertEqual(result.returncode,0)
                    page.wait_for_function('() => (document.querySelector("#private-result").hidden === false)',timeout=30000)
                    self.assertIn('1800.00',page.locator('#private-dimensions').inner_text())
                    self.assertIn('NEEDS_REVIEW',page.locator('#private-qa').inner_text())
                    self.assertIn('false',page.locator('#private-qa').inner_text())
                    self.assertIn('AI',page.locator('#connection-state').inner_text())
                    with page.expect_download() as download:
                        page.get_by_role('button',name='Tải BLEND riêng tư',exact=True).click()
                    saved=root/'download.blend';download.value.save_as(saved);self.assertTrue(saved.read_bytes().startswith(b'BLENDER'))
                    page.locator('#model-instruction').fill('Dựng lại từ cùng chứng cứ, giữ bản gốc')
                    page.locator('#rebuild-job').click();page.wait_for_function('() => (document.querySelector("#job-state").textContent.includes("WAITING_ANALYSIS"))')
                    new_jobs=httpx.get('http://127.0.0.1:8773/jobs',headers=owner).json();self.assertEqual(len(new_jobs),2)
                    self.assertNotEqual(new_jobs[0]['id'],jid)
                    page.locator('#local-logout').click()
                    self.assertTrue(page.locator('#private-result').is_hidden());self.assertTrue(page.locator('#create-job').is_disabled())
                    self.assertEqual(page.evaluate('localStorage.length+sessionStorage.length'),0)
                    self.assertEqual(errors,[])
                    browser.close()
            finally:
                process.terminate();process.wait(timeout=10)
