import hashlib,hmac,json,os,re,uuid
from pathlib import Path
from fastapi import FastAPI,Depends,File,Form,UploadFile,HTTPException,Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from PIL import Image,UnidentifiedImageError
from .store import Store
from hgcloud.intake import INPUT_TYPES,compile_scene
from hgcloud.core import SceneError
from hgcloud.vision import ROLES
MAX_IMAGE=20*1024*1024

def create_app(root,credentials):
    if not credentials or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,50}',u) or len(t)<32 for u,t in credentials.items()):
        raise ValueError('Unique user credentials with >=32 character random tokens are required')
    if len(set(credentials.values()))!=len(credentials):raise ValueError('Tokens must be unique per user')
    hashed={u:hashlib.sha256(t.encode()).digest() for u,t in credentials.items()}
    store=Store(root);security=HTTPBearer(auto_error=False)
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None);app.state.store=store
    @app.exception_handler(OverflowError)
    async def quota_error(request,exc):
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':'Active job limit reached'},status_code=429)
    def authenticate(auth:HTTPAuthorizationCredentials=Depends(security)):
        if not auth or auth.scheme.lower()!='bearer':raise HTTPException(401,'Authentication required',headers={'WWW-Authenticate':'Bearer'})
        digest=hashlib.sha256(auth.credentials.encode()).digest();owner=None
        for name,value in hashed.items():
            if hmac.compare_digest(digest,value):owner=name
        if owner is None:raise HTTPException(401,'Invalid credential')
        return owner
    def owned(jid,user):
        try:return store.get(jid,user)
        except KeyError:raise HTTPException(404,'Job not found')
    def public(job):
        return {k:job[k] for k in ['id','state','created','error']}|{'instruction':job['payload']['instruction'],
            'progress':None,'review_status':'NEEDS_REVIEW','analysis_mode':'supervised','roles':ROLES}
    @app.middleware('http')
    async def safe_response(request:Request,call_next):
        from fastapi.responses import JSONResponse
        if request.url.hostname not in {'127.0.0.1','localhost','::1'}:
            return JSONResponse({'detail':'Loopback host required'},status_code=403)
        origin=request.headers.get('origin')
        if request.method=='POST' and origin and origin!=str(request.base_url).rstrip('/'):
            return JSONResponse({'detail':'Same-origin request required'},status_code=403)
        # Bound whole multipart/JSON body before parsing; no public CORS access.
        from fastapi.responses import JSONResponse
        # Only reviewed static local UI files are public; private API remains bearer-only.
        if request.method in {'GET','HEAD'} and request.url.path.startswith('/local/'):
            response=await call_next(request)
            response.headers['Cache-Control']='no-store'
            response.headers['X-Content-Type-Options']='nosniff'
            response.headers['Referrer-Policy']='no-referrer'
            return response
        auth=request.headers.get('authorization','').split(' ',1)
        if len(auth)!=2 or auth[0].lower()!='bearer' or not any(hmac.compare_digest(hashlib.sha256(auth[1].encode()).digest(),v) for v in hashed.values()):
            return JSONResponse({'detail':'Authentication required'},status_code=401,headers={'WWW-Authenticate':'Bearer','Cache-Control':'no-store'})
        length=request.headers.get('content-length')
        try:bad=length is not None and (int(length)<0 or int(length)>MAX_IMAGE+1024*1024)
        except ValueError:bad=True
        if bad:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Request too large or invalid length'},status_code=413)
        if request.method=='POST' and length is None:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Content-Length required'},status_code=411)
        if request.method=='POST':
            chunks=bytearray()
            async for chunk in request.stream():
                chunks.extend(chunk)
                if len(chunks)>MAX_IMAGE+1024*1024:
                    return JSONResponse({'detail':'Request too large'},status_code=413)
            request._body=bytes(chunks)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
        return response
    @app.get('/capabilities')
    def capabilities(user=Depends(authenticate)):
        import shutil
        return {'authenticated':True,'privateStorage':True,'blender':bool(shutil.which('blender')),
                'vision':False,'connected':False,'analysis_mode':'supervised','status':'CHƯA KẾT NỐI AI tự động','roles':ROLES}
    @app.post('/jobs',status_code=201)
    async def upload(image:UploadFile=File(...),input_type:str=Form(...),instruction:str=Form(''),user=Depends(authenticate)):
        if input_type not in INPUT_TYPES or len(instruction)>4000:raise HTTPException(422,'Invalid request')
        data=await image.read(MAX_IMAGE+1);await image.close()
        if not data or len(data)>MAX_IMAGE:raise HTTPException(413,'Image must be <=20 MiB')
        import io
        try:
            with Image.open(io.BytesIO(data)) as im:
                fmt=im.format;size=im.size
                if fmt not in {'PNG','JPEG','WEBP'} or size[0]*size[1]>25_000_000:raise ValueError()
                im.verify()
        except (ValueError,OSError,Image.DecompressionBombError):raise HTTPException(422,'Invalid or unsupported image')
        with store.connect() as c:
            count=c.execute("SELECT count(*) FROM jobs WHERE owner=? AND state NOT IN ('FAILED','NEEDS_REVIEW','INTERRUPTED')",(user,)).fetchone()[0]
        if count>=20:raise HTTPException(429,'Active job limit reached')
        jid=store.create(user,{'input_type':input_type,'instruction':instruction,'source_sha256':hashlib.sha256(data).hexdigest()})
        folder=store.folder(jid);suffix={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[fmt]
        source=folder/('source'+suffix);source.write_bytes(data);source.chmod(0o600)
        (folder/'intake.json').write_text(json.dumps({'source':source.name,'sha256':hashlib.sha256(data).hexdigest(),'pixels':list(size),'input_type':input_type}))
        store.transition(jid,'WAITING_ANALYSIS');return public(store.get(jid,user))
    @app.get('/jobs')
    def jobs(user=Depends(authenticate)):
        with store.connect() as c:rows=c.execute('SELECT id FROM jobs WHERE owner=? ORDER BY created DESC LIMIT 50',(user,)).fetchall()
        return [public(store.get(r['id'],user)) for r in rows]
    @app.get('/jobs/{jid}')
    def job(jid:str,user=Depends(authenticate)):return public(owned(jid,user))
    @app.get('/jobs/{jid}/source')
    def source(jid:str,user=Depends(authenticate)):
        j=owned(jid,user);folder=store.folder(jid);m=json.loads((folder/'intake.json').read_text())
        return FileResponse(folder/m['source'],filename=m['source'])
    @app.post('/jobs/{jid}/observations',status_code=202)
    def observations(jid:str,body:dict,user=Depends(authenticate)):
        owned(jid,user)
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT state FROM jobs WHERE id=?',(jid,)).fetchone()
            if row['state']!='WAITING_ANALYSIS':raise HTTPException(409,'Job already submitted; create a revision')
            folder=store.folder(jid);op=folder/'observations.json'
            if len(json.dumps(body))>512_000:raise HTTPException(413,'Observations too large')
            op.write_text(json.dumps(body,ensure_ascii=False))
            try:
                scene=compile_scene(folder/'intake.json',op)
                if len(scene['objects'])>100:raise SceneError('Maximum 100 objects')
                for o in scene['objects']:
                    if max(o['size_mm'])>100000 or max(abs(v) for v in o['center_mm'])>100000:raise SceneError('Scene exceeds limits')
            except (SceneError,KeyError,TypeError,ValueError,AttributeError,IndexError):raise HTTPException(422,'Invalid observations; unresolved dimensions or evidence')
            scene['analysis_mode']='human_reviewed_image';scene['render_allowed']=False
            (folder/'scene.json').write_text(json.dumps(scene,ensure_ascii=False))
            c.execute("UPDATE jobs SET state='QUEUED' WHERE id=?",(jid,))
        return public(store.get(jid,user))
    @app.post('/jobs/{jid}/revisions',status_code=201)
    def revise(jid:str,body:dict,user=Depends(authenticate)):
        base=owned(jid,user);instruction=body.get('instruction')
        if not isinstance(instruction,str) or not 1<=len(instruction)<=4000:raise HTTPException(422,'Revision instruction required')
        if base['state'] not in {'NEEDS_REVIEW','FAILED','INTERRUPTED'}:raise HTTPException(409,'Base job is not finished')
        with store.connect() as c:
            active=c.execute("SELECT count(*) FROM jobs WHERE owner=? AND state NOT IN ('FAILED','NEEDS_REVIEW','INTERRUPTED')",(user,)).fetchone()[0]
        if active>=20:raise HTTPException(429,'Active job limit reached')
        new=store.create(user,base['payload']|{'instruction':instruction,'parent_job':jid})
        import shutil
        old,folder=store.folder(jid),store.folder(new)
        m=json.loads((old/'intake.json').read_text())
        shutil.copyfile(old/m['source'],folder/m['source']);shutil.copyfile(old/'intake.json',folder/'intake.json')
        store.transition(new,'WAITING_ANALYSIS');return public(store.get(new,user))
    @app.get('/jobs/{jid}/artifacts/{kind}')
    def artifact(jid:str,kind:str,user=Depends(authenticate)):
        j=owned(jid,user)
        if kind not in {'glb','blend','qa','html'}:raise HTTPException(404,'Artifact not found')
        if j['state']!='NEEDS_REVIEW':raise HTTPException(409,'Artifact not ready')
        folder=store.folder(jid);receipt=json.loads((folder/'result.json').read_text());run=receipt['run']
        if not re.fullmatch(r'run-[0-9a-f]{32}',run):raise HTTPException(500,'Invalid artifact reference')
        filename={'glb':'hg_scene.glb','blend':'hg_scene.blend','qa':'qa_report.json','html':'qa_report.html'}[kind]
        path=folder/run/filename
        item=receipt.get('artifacts',{}).get(filename,{})
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=item.get('bytes') or hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('sha256'):
            raise HTTPException(409,'Artifact integrity verification failed; operator review required')
        return FileResponse(path,filename=filename,media_type={'glb':'model/gltf-binary','blend':'application/octet-stream','qa':'application/json','html':'text/html'}[kind])
    @app.get('/local/{file:path}')
    def local_ui(file:str):
        from fastapi.responses import HTMLResponse
        base=Path(__file__).resolve().parents[2]/'viewer'
        dist=base/'dist'
        if file in {'local-client.js','local-style.css'}:
            return FileResponse(base/file,media_type='text/javascript' if file.endswith('.js') else 'text/css')
        if not (dist/'build-manifest.json').exists():raise HTTPException(503,'Build viewer first')
        allowed={f['path'] for f in json.loads((dist/'build-manifest.json').read_text())['files']}
        if file in {'','index.html'}:
            html=(dist/'index.html').read_text()
            html=html.replace('</head>','<link rel="stylesheet" href="local-style.css"></head>')
            html=html.replace('</body>','<script type="module" src="local-client.js"></script></body>')
            return HTMLResponse(html)
        if file not in allowed or '..' in Path(file).parts:raise HTTPException(404,'Not found')
        return FileResponse(dist/file)
    return app
