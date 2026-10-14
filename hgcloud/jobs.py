"""Safe, independent jobs and immutable input snapshots."""
import json, shutil
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from .core import load, save_report

def create_job(scene_path,root='jobs'):
    scene=load(scene_path)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    jid=f'HG3D-{stamp}-{uuid4().hex[:8]}'
    folder=Path(root).resolve()/jid
    folder.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(scene_path,folder/'scene.json')
    report=save_report(scene,folder/'qa_report.json')
    state={'job_id':jid,'status':'PREPARED','created_utc':stamp,
           'cloud_rendering':False,'review_status':report['status'],
           'blender_executed':False,'artifacts':[]}
    (folder/'job.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    return folder
