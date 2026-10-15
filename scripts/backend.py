"""Local authenticated API/worker; credentials never belong in Git or Pages."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
p=argparse.ArgumentParser();p.add_argument('mode',choices=['init','api','worker']);p.add_argument('--root',default='.private/backend');p.add_argument('--credentials',default='.private/backend-credentials.json');p.add_argument('--port',type=int,default=8770);p.add_argument('--once',action='store_true');a=p.parse_args()
os.umask(0o077)
if a.mode=='init':
    import secrets
    path=Path(a.credentials);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open('x') as f:json.dump({'local-user':secrets.token_urlsafe(48)},f)
    path.chmod(0o600);print('Local credential file created. Read it securely; never paste tokens in chat.')
elif a.mode=='api':
    import uvicorn
    from hgcloud.backend.api import create_app
    credentials=json.loads(Path(a.credentials).read_text())
    uvicorn.run(create_app(a.root,credentials),host='127.0.0.1',port=a.port,access_log=False)
else:
    from hgcloud.backend.worker import serve_worker
    serve_worker(a.root,a.once)
