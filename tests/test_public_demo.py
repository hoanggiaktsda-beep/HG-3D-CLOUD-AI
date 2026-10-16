"""Negative publication gates. These fixtures do not prove successful AI inference."""
import json,tempfile,unittest
from pathlib import Path
from scripts.package_public_demo import package
class PublicDemoGateTests(unittest.TestCase):
 def test_replay_or_partial_experiment_cannot_be_published(self):
  with tempfile.TemporaryDirectory() as td:
   source=Path(td)/'source';source.mkdir();out=Path(td)/'published'
   for status in ['offline_replay','FAILED','STARTED']:
    (source/'trial.json').write_text(json.dumps({'status':status,'render_executed':False,'results':[]}))
    with self.subTest(status=status),self.assertRaises(ValueError):package(source,out,'123','a'*40)
    self.assertFalse(out.exists())
 def test_arbitrary_identity_and_missing_catalog_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   source=Path(td)/'source';source.mkdir();out=Path(td)/'published'
   (source/'trial.json').write_text(json.dumps({'status':'EXPERIMENT_COMPLETED_NOT_FINAL_APPROVAL','render_executed':False,'results':[]}))
   for run,commit in [('../private','a'*40),('123','main'),('123','a'*40)]:
    with self.subTest(run=run,commit=commit),self.assertRaises(ValueError):package(source,out,run,commit)
    self.assertFalse(out.exists())
