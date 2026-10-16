"""Publish ONLY fixed public Qwen cases after actual inference and Blender QA.
Never accepts a customer's image, arbitrary URL, or arbitrary artifact path.
"""
import argparse,hashlib,json,os,re,shutil,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.public_assembly_trial import CASES,REVISION
from hgcloud.assembly_evidence import verified_reading,agree_calibration
from hgcloud.vision import ROLES

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def package(source,output,run_id,commit):
 source,output=Path(source),Path(output)
 if not re.fullmatch(r'[0-9]+',str(run_id)) or not re.fullmatch(r'[a-f0-9]{40}',commit):raise ValueError('Immutable GitHub run and commit required')
 trial=json.loads((source/'trial.json').read_text())
 if trial['status']!='EXPERIMENT_COMPLETED_NOT_FINAL_APPROVAL' or trial.get('render_executed') is not False:raise ValueError('Actual experiment did not complete safely')
 if {r['case'] for r in trial['results']}!={c['id'] for c in CASES}:raise ValueError('Public catalog mismatch')
 output.mkdir(parents=True,exist_ok=False)
 release={'schema':1,'scope':'fixed_public_qwen_catalog_only','run_id':str(run_id),'commit':commit,
  'run_url':f'https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/{run_id}',
  'roles':ROLES,'model_revision':REVISION,'test30_status':'CẦN XÁC NHẬN','final_approved':False,
  'private_upload_connected':False,'cases':[],'files':[]}
 readings_out={}
 for case in CASES:
  folder=source/case['id'];summary=next(r for r in trial['results'] if r['case']==case['id'])
  info=json.loads((folder/'source.json').read_text())
  if info['sha256']!=case['sha256'] or sha(folder/'public-source.pdf')!=case['sha256']:raise ValueError('Unapproved public document')
  readings=json.loads((folder/'readings.json').read_text())
  if not readings or summary.get('live_model_executed') is not True:raise ValueError('No actual inference')
  for reading in readings:verified_reading(reading,case['sha256'])
  readings_out[case['id']]=[{k:r[k] for k in ['purpose','page','image_sha256','ai_text','ocr_text','execution']} for r in readings]
  record={'id':case['id'],'status':summary['status'],'source':info,'assembly_allowed':False,
    'review_status':'CẦN XÁC NHẬN','reason':summary.get('reason'),'artifacts':{}}
  if summary['outputs_created']:
   if case['id']!='chair' or summary['status']!='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW' or summary.get('assembly_allowed') is not False:raise ValueError('Only reviewed chair cut-layout output can be public')
   agree_calibration(readings,case['sha256'])
   qa=json.loads((folder/'build/part_qa.json').read_text())
   if qa.get('technical_status')!='PASS' or qa.get('render_executed') is not False or qa.get('assembly_verified') is not False or qa.get('blend_reopen')!='PASS' or qa.get('glb_reimport')!='PASS' or not qa.get('parts') or not all(r.get('passed') is True for r in qa['parts']):raise ValueError('Blender evidence failed')
   data=(folder/'build/cut_layout.glb').read_bytes()
   if struct.unpack('<4sII',data[:12])!=(b'glTF',2,len(data)):raise ValueError('Invalid GLB')
   gltf=json.loads(data[20:20+struct.unpack('<I',data[12:16])[0]].decode().strip())
   if any(v.get('uri') for v in gltf.get('buffers',[])+gltf.get('images',[])):raise ValueError('External GLB resources forbidden')
   if not (folder/'build/cut_layout.blend').read_bytes().startswith(b'BLENDER'):raise ValueError('Invalid BLEND')
   for source_name,target in [('cut_layout.glb','chair.glb'),('cut_layout.blend','chair.blend'),('part_qa.json','chair-qa.json')]:
    path=folder/'build'/source_name
    if path.is_symlink() or path.stat().st_size>25*1024*1024:raise ValueError('Unsafe public asset')
    shutil.copyfile(path,output/target);record['artifacts'][target.split('.')[-1]]='public-demo/'+target
   record['parts']=summary['parts'];record['min_source_top_iou']=summary['min_source_top_iou']
   record['source_uncertainty_mm']=summary['source_uncertainty_mm'];record['warnings']=summary['source_warnings']
  elif summary['status']!='BLOCKED_NEEDS_CONFIRMATION':raise ValueError('Unexpected public state')
  release['cases'].append(record)
 (output/'readings.json').write_text(json.dumps(readings_out,ensure_ascii=False,indent=2))
 release['files']=[{'path':'public-demo/'+p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(output.iterdir())]
 (output/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2))
 return release
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--run-id',required=True);p.add_argument('--commit',required=True);a=p.parse_args()
 print(json.dumps(package(a.source,a.output,a.run_id,a.commit),ensure_ascii=False))
