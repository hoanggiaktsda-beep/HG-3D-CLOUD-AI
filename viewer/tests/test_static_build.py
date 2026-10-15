import hashlib,json,subprocess,tempfile,unittest,shutil
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[2]
class StaticBuildTests(unittest.TestCase):
    def test_allowlist_integrity_no_private_files(self):
        dist=ROOT/'viewer/dist';manifest=json.loads((dist/'build-manifest.json').read_text())
        actual={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
        listed={f['path'] for f in manifest['files']}|{'build-manifest.json'}
        self.assertEqual(actual,listed);self.assertEqual(len(actual),16)
        self.assertEqual(manifest['base_path'],'/HG-3D-CLOUD-AI/')
        for f in manifest['files']:
            self.assertEqual(hashlib.sha256((dist/f['path']).read_bytes()).hexdigest(),f['sha256'])
        self.assertFalse(any(p.endswith(('.png','.blend','.pdf')) or p.startswith(('inputs/','outputs/','node_modules/')) for p in actual))
        self.assertNotIn('node_modules',(dist/'index.html').read_text())
        self.assertTrue((dist/'.nojekyll').is_file());self.assertTrue((dist/'vendor/three/LICENSE').is_file())
    def test_repeatable_build(self):
        path=ROOT/'viewer/dist/build-manifest.json';before=path.read_bytes()
        result=subprocess.run(['node','build.mjs'],cwd=ROOT/'viewer',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertEqual(path.read_bytes(),before)
    def test_unreviewed_asset_changes_are_blocked(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='public-build-test-') as folder:
            folder=Path(folder);(folder/'assets').mkdir()
            shutil.copy(ROOT/'viewer/build.mjs',folder/'build.mjs');shutil.copy(ROOT/'viewer/public-assets.json',folder/'public-assets.json')
            (folder/'assets/sample.glb').write_bytes(b'private replacement')
            shutil.copy(ROOT/'viewer/assets/sample-qa.json',folder/'assets/sample-qa.json')
            result=subprocess.run(['node','build.mjs'],cwd=folder,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('without review',result.stderr);self.assertFalse((folder/'dist').exists())

    def test_missing_public_hash_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='missing-hash-test-') as folder:
            folder=Path(folder)
            shutil.copy(ROOT/'viewer/build.mjs',folder/'build.mjs')
            manifest=json.loads((ROOT/'viewer/public-assets.json').read_text())
            manifest['assets']=manifest['assets'][:1]
            (folder/'public-assets.json').write_text(json.dumps(manifest))
            result=subprocess.run(['node','build.mjs'],cwd=folder,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Both public sample hashes required',result.stderr)
            self.assertFalse((folder/'dist').exists())
