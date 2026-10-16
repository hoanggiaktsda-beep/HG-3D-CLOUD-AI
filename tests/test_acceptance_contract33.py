"""Prevent the public acceptance workflow from accepting customer uploads or paid runners."""
import unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
class AcceptanceContract33Tests(unittest.TestCase):
 def setUp(self):
  self.workflow=yaml.load((ROOT/'.github/workflows/test33-acceptance.yml').read_text(),Loader=yaml.BaseLoader)
 def test_public_only_standard_cpu_and_bounded_runs(self):
  w=self.workflow
  self.assertEqual(w['permissions'],{'contents':'read'})
  self.assertEqual(set(w['on']),{'push','workflow_dispatch'})
  self.assertEqual(w['on']['push']['branches'],['main'])
  self.assertFalse(w['on']['workflow_dispatch']) # no uploads, URLs or commands as inputs
  for job in w['jobs'].values():
   self.assertEqual(job['runs-on'],'ubuntu-24.04')
   self.assertIn("github.repository == 'hoanggiaktsda-beep/HG-3D-CLOUD-AI'",job['if'])
   self.assertIn('github.event.repository.private == false',job['if'])
   self.assertLessEqual(int(job['timeout-minutes']),20)
 def test_artifact_allowlist_excludes_private_jobs_and_model_weights(self):
  uploads=[s for j in self.workflow['jobs'].values() for s in j['steps'] if s.get('uses','').startswith('actions/upload-artifact@')]
  self.assertEqual(len(uploads),2)
  for s in uploads:
   self.assertEqual(s['with']['retention-days'],'1')
   for path in s['with']['path'].splitlines():
    self.assertTrue(path.startswith('${{ runner.temp }}/test33-'))
    self.assertNotIn('model-cache',path)
    self.assertNotIn('.private',path)
    self.assertNotIn('outputs',path)
  live=self.workflow['jobs']['live-vision']['steps']
  self.assertTrue(any(s.get('run','').startswith('python scripts/public_assembly_trial.py --output') for s in live))
