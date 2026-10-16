"""Recover metric anchors only from reviewed homologous top/front/side annotations.
This is a supervised consistency solver, not AI part recognition or final approval.
"""
import math
from .core import SceneError
from .assembly_constraints import VIEW_AXES,verify_placement

def anchors_from_views(views,anchor_ids,tolerance_mm):
 if not isinstance(views,dict) or set(views)!=set(VIEW_AXES) or type(tolerance_mm) not in (float,int) or not 0<tolerance_mm<=5:raise SceneError('Missing views or invalid tolerance')
 if not isinstance(anchor_ids,list) or any(not isinstance(a,str) or not a for a in anchor_ids) or len(anchor_ids)<3 or len(set(anchor_ids))!=len(anchor_ids):raise SceneError('Three unique corresponding anchors required')
 if any(not isinstance(v,dict) or not isinstance(v.get('metric_frame_id'),str) for v in views.values()):raise SceneError('Invalid view annotations or metric frame')
 frames={v.get('metric_frame_id') for v in views.values()}
 if len(frames)!=1 or not next(iter(frames)):raise SceneError('Views do not share an explicitly reviewed metric frame')
 for view in views.values():
  if view.get('status')!='confirmed' or view.get('basis')!='reviewed_metric_annotation' or set(view.get('anchors_mm',{}))!=set(anchor_ids):raise SceneError('Unreviewed or missing homologous image anchors')
 world=[]
 for anchor in anchor_ids:
  axes=[[],[],[]]
  for name,mapping in VIEW_AXES.items():
   values=views[name]['anchors_mm'][anchor]
   if not isinstance(values,list) or len(values)!=2 or any(type(x) not in (float,int) or not math.isfinite(x) for x in values):raise SceneError('Invalid metric view anchor')
   for axis,value in zip(mapping,values):axes[axis].append(value)
  if any(max(values)-min(values)>tolerance_mm for values in axes):raise SceneError('Contradictory anchor coordinates between views')
  world.append([sum(values)/len(values) for values in axes])
 return world

def solve_reviewed_placement(part,proposal,source_sha256,document_sha256):
 proposal=dict(proposal)
 proposal['world_anchors_mm']=anchors_from_views(proposal.get('views',{}),proposal.get('anchor_ids',[]),proposal.get('tolerance_mm',0))
 if len(proposal.get('local_anchors_mm',[]))!=len(proposal.get('anchor_ids',[])):raise SceneError('Local anchor mapping is incomplete')
 result=verify_placement(part,proposal,source_sha256,document_sha256)
 return dict(result,anchor_basis='reviewed_homologous_top_front_side',final_approved=False,status='CẦN XÁC NHẬN')
