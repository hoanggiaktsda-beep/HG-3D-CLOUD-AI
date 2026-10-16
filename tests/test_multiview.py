"""Synthetic metric constraints verify math, not successful AI reading of a drawing."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from hgcloud.multiview import anchors_from_views,solve_reviewed_placement
from hgcloud.core import SceneError
class MultiviewTests(unittest.TestCase):
 def data(self,folder):
  image=Path(folder)/'public-synthetic-view';image.write_bytes(b'Synthetic correspondence evidence, not an AI output')
  digest=hashlib.sha256(image.read_bytes()).hexdigest();world=[[100,200,300],[100,220,300],[80,200,300]]
  views={}
  for name,axes in {'top':(0,1),'front':(0,2),'side':(1,2)}.items():
   # Rotated 20x20x2 plate about Z; bounding boxes include thickness.
   bounds={'top':[80,200,100,220],'front':[80,299,100,301],'side':[200,299,220,301]}[name]
   views[name]={'status':'confirmed','basis':'reviewed_metric_annotation','metric_frame_id':'fixture-mm-XYZ','source_note':'Synthetic math fixture only','anchors_mm':{k:[p[i] for i in axes] for k,p in zip('abc',world)},'bbox_mm':bounds,'image_path':str(image),'image_sha256':digest,'document_sha256':'public-doc'}
  proposal={'source_sha256':'source','semantic_assignment_status':'confirmed','semantic_label':'synthetic plate','anchor_review_status':'confirmed','anchor_source_note':'Explicit synthetic anchor mapping','local_anchors_mm':[[0,0,0],[20,0,0],[0,20,0]],'anchor_ids':['a','b','c'],'views':views,'tolerance_mm':.1}
  part={'thickness_mm':2,'outline_mm':[[0,0],[20,0],[20,20],[0,20]]}
  return part,proposal
 def test_rotated_placement_is_recovered_from_three_reviewed_views(self):
  with tempfile.TemporaryDirectory() as td:
   part,p=self.data(td);r=solve_reviewed_placement(part,p,'source','public-doc')
   self.assertLess(r['anchor_residual_mm'],.00001);self.assertEqual(r['translation_mm'],[100,200,300]);self.assertFalse(r['final_approved'])
 def test_missing_conflicting_unreviewed_or_modified_views_block(self):
  with tempfile.TemporaryDirectory() as td:
   part,base=self.data(td)
   for change in ['missing','conflict','unreviewed','mixed_frame','changed_image','wrong_document']:
    p=copy.deepcopy(base)
    if change=='missing':del p['views']['side']
    if change=='conflict':p['views']['front']['anchors_mm']['a'][0]+=10
    if change=='unreviewed':p['views']['top']['status']='inferred'
    if change=='mixed_frame':p['views']['top']['metric_frame_id']='other'
    if change=='changed_image':p['views']['top']['image_sha256']='changed'
    if change=='wrong_document':p['views']['side']['document_sha256']='other'
    with self.subTest(change=change),self.assertRaises(SceneError):solve_reviewed_placement(part,p,'source','public-doc')
