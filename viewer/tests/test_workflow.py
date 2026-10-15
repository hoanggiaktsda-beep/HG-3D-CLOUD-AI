"""Static deployment contract checks; these do not claim GitHub deployment success."""
import unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
class PagesWorkflowTests(unittest.TestCase):
    def test_only_project_main_and_reviewed_artifact_can_deploy(self):
        path=ROOT/'.github/workflows/deploy-pages.yml'
        workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['on']['push']['branches'],['main'])
        self.assertIn('workflow_dispatch',workflow['on'])
        build=workflow['jobs']['build'];deploy=workflow['jobs']['deploy']
        self.assertEqual(deploy['needs'],'build')
        artifacts=[s for s in build['steps'] if s.get('uses','').startswith('actions/upload-pages-artifact@')]
        self.assertEqual(len(artifacts),1);self.assertEqual(artifacts[0]['with']['path'],'viewer/dist')
        runs=[s for s in build['steps'] if 'run' in s]
        self.assertTrue(any('npm ci --ignore-scripts' in s['run'] for s in runs))
        self.assertTrue(any(s['run']=='npm run build' for s in runs))
        self.assertTrue(all(s['working-directory']=='viewer' for s in runs))
        self.assertEqual(deploy['environment']['name'],'github-pages')
        self.assertEqual(workflow['permissions'],{'contents':'read','pages':'write','id-token':'write'})
        self.assertTrue(any(s.get('uses','').startswith('actions/deploy-pages@') for s in deploy['steps']))
        self.assertFalse((ROOT/'viewer/pages-workflow.example.yml').exists())
