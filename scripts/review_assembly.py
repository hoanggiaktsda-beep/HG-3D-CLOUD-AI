"""Supervised multiview placement review; never builds hidden hardware or renders."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hgcloud.multiview import solve_reviewed_placement
from hgcloud.vision import ROLES
from hgcloud.core import SceneError

def review(layout,plan):
 approved,blocked={},{}
 for part in layout['parts']:
  try:approved[part['id']]=solve_reviewed_placement(part,plan.get('placements',{})[part['id']],layout['source_sha256'],layout['document_sha256'])
  except (SceneError,KeyError,ValueError,TypeError,OSError) as e:blocked[part['id']]={'status':'CẦN XÁC NHẬN','reason':str(e)}
 return {'status':'PLACEMENT_CANDIDATES_NEEDS_REVIEW' if approved and not blocked else 'BLOCKED_MISSING_PLACEMENT_EVIDENCE','placements':approved,'blocked':blocked,'roles':ROLES,'final_approved':False,'physical_bores_created':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('layout',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 with a.output.open('x') as f:json.dump(review(json.loads(a.layout.read_text()),json.loads(a.plan.read_text())),f,ensure_ascii=False,indent=2)
