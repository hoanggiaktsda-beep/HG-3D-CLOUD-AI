"""Install only the fixed public release, then let build.mjs validate all pins/hashes.
Used by the public workflow; never stages the whole checkout or any private file.
"""
import argparse,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES={'release.json','readings.json','chair.glb','chair.blend','chair-qa.json'}
def install(source):
 source=Path(source);target=ROOT/'viewer/public-demo'
 actual={p.name for p in source.iterdir()}
 if not {'release.json','readings.json'}<=actual or not actual<=NAMES or any(p.is_symlink() or not p.is_file() for p in source.iterdir()):raise ValueError('Unapproved public release files')
 release=json.loads((source/'release.json').read_text())
 expected={Path(f['path']).name for f in release['files']}|{'release.json'}
 if expected!=actual:raise ValueError('Release receipt mismatch')
 if target.is_symlink():raise ValueError('Unsafe publication folder')
 target.mkdir(exist_ok=True)
 if any(p.name not in NAMES or p.is_symlink() or not p.is_file() for p in target.iterdir()):raise ValueError('Refuse touching unknown release files')
 for name in NAMES:
  if (source/name).exists():shutil.copyfile(source/name,target/name)
  elif (target/name).exists():(target/name).unlink() # Only a previous generated catalog asset, versioned in Git.
 return target
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--stage',action='store_true');a=p.parse_args()
 target=install(a.source)
 subprocess.run(['node','build.mjs'],cwd=ROOT/'viewer',check=True)
 if a.stage:
  for name in sorted(NAMES):
   path='viewer/public-demo/'+name
   tracked=subprocess.run(['git','ls-files','--error-unmatch','--',path],cwd=ROOT,capture_output=True).returncode==0
   if (ROOT/path).exists() or tracked:subprocess.run(['git','add','--',path],cwd=ROOT,check=True)
