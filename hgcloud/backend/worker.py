"""Single local Blender worker, persisted SQLite claim, no user code execution."""
import fcntl,hashlib,json,os,signal,subprocess,time,uuid
from pathlib import Path
from .store import Store
ROOT=Path(__file__).resolve().parents[2]

def command(args,log,timeout=120):
    with log.open('ab') as output:
        process=subprocess.Popen(args,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            if process.wait(timeout=timeout):raise RuntimeError('Blender command failed')
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait();raise RuntimeError('Blender timeout')

def run_once(store):
    job=store.claim()
    if not job:return False
    folder=store.folder(job['id']);run='run-'+uuid.uuid4().hex;build=folder/run
    try:
        for script in ['blender_build.py','verify_blender.py']:
            command(['blender','-b','-t','2','--python-exit-code','1','--python',str(ROOT/'scripts'/script),'--',str(folder/'scene.json'),str(build)],folder/'worker.log')
        # Reopen saved BLEND and independently reimport actual GLB before publication.
        command(['blender','-b','-t','2','--python-exit-code','1','--python',str(ROOT/'scripts/blender_job_interchange.py'),'--',str(build)],folder/'worker.log')
        interchange=json.loads((build/'interchange_qa.json').read_text())
        if interchange.get('status')!='PASS' or not interchange.get('blend_reopen') or not interchange.get('glb_reimport'):
            raise RuntimeError('Interchange verification failed')
        qa=json.loads((build/'qa_report.json').read_text())
        qa['interchange_validation']=interchange
        if qa.get('geometry_status')!='PASS' or not qa['blender_details']['glb_created'] or qa['blender_details']['glb_error']:
            raise RuntimeError('Verification failed')
        if not (build/'hg_scene.blend').is_file() or not (build/'hg_scene.glb').is_file():raise RuntimeError('Missing artifacts')
        # Build success never grants approval, even if the input had only confirmed measures.
        qa['status']='NEEDS_REVIEW';qa['analysis_mode']='human_reviewed_image';qa['automatic_vision_executed']=False
        (build/'qa_report.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
        from hgcloud.preview import build_html
        build_html(build/'qa_report.json',build/'qa_report.html')
        artifacts={name:{'sha256':hashlib.sha256((build/name).read_bytes()).hexdigest(),'bytes':(build/name).stat().st_size} for name in ['hg_scene.glb','hg_scene.blend','qa_report.json','qa_report.html']}
        (folder/'result.json').write_text(json.dumps({'run':run,'artifacts':artifacts}))
        store.transition(job['id'],'NEEDS_REVIEW')
    except Exception:
        store.transition(job['id'],'FAILED','Worker failed; operator can inspect private log')
    return True

def serve_worker(root,once=False):
    os.umask(0o077);store=Store(root)
    with (store.root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Exclusive worker ownership: previous RUNNING jobs cannot be called successful.
        with store.connect() as c:c.execute("UPDATE jobs SET state='INTERRUPTED',error='Worker interrupted; create revision' WHERE state='RUNNING'")
        while True:
            worked=run_once(store)
            if once:return
            if not worked:time.sleep(.5)
