"""Public product workflow cannot become a customer upload endpoint or paid runner."""
import unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
class PublicWorkflowTests(unittest.TestCase):
 def test_no_customer_inputs_paid_runner_or_model_upload(self):
  w=yaml.load((ROOT/'.github/workflows/public-demo.yml').read_text(),Loader=yaml.BaseLoader)
  self.assertFalse(w['on']['workflow_dispatch']);self.assertNotIn('pull_request',w['on']);self.assertNotIn('schedule',w['on'])
  self.assertEqual(w['concurrency']['group'],'pages')
  self.assertEqual(w['permissions'],{'contents':'read'})
  self.assertIn('github.event.repository.private == false',w['jobs']['infer']['if'])
  for job in w['jobs'].values():
   self.assertEqual(job['runs-on'],'ubuntu-24.04');self.assertLessEqual(int(job['timeout-minutes']),20)
  infer=w['jobs']['infer']['steps']
  self.assertTrue(any(s.get('run','').startswith('python scripts/public_assembly_trial.py ') for s in infer))
  uploads=[s for s in infer if s.get('uses','').startswith('actions/upload-artifact@')]
  self.assertEqual(uploads[0]['with']['path'],'${{ runner.temp }}/public-release/')
  self.assertEqual(uploads[0]['with']['retention-days'],'1')
  self.assertEqual(w['jobs']['publish']['permissions'],{'contents':'write'})
  self.assertEqual(w['jobs']['deploy']['permissions'],{'contents':'read','pages':'write','id-token':'write'})
  self.assertTrue(any(s.get('run')=='python scripts/verify_public_demo.py' for s in w['jobs']['verify']['steps']))
