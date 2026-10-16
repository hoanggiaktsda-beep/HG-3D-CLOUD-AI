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
        # Serialized deployments must include the latest verified bot-published release.
        for job in [build,workflow['jobs']['verify']]:
            checkout=next(s for s in job['steps'] if s.get('uses','').startswith('actions/checkout@'))
            self.assertEqual(checkout['with']['ref'],'main')

    def test_test32_checks_gate_deployment_and_verify_actual_site(self):
        workflow=yaml.load((ROOT/'.github/workflows/deploy-pages.yml').read_text(),Loader=yaml.BaseLoader)
        steps=workflow['jobs']['build']['steps']
        test_index=next(i for i,s in enumerate(steps) if 'unittest discover' in s.get('run',''))
        upload_index=next(i for i,s in enumerate(steps) if s.get('uses','').startswith('actions/upload-pages-artifact@'))
        self.assertLess(test_index,upload_index)
        verify=workflow['jobs']['verify'];self.assertEqual(verify['needs'],'deploy')
        self.assertTrue(any(s.get('run')=='python scripts/verify_pages32.py' for s in verify['steps']))
        text=(ROOT/'scripts/verify_pages32.py').read_text()
        for check in ['hashlib.sha256','expect_download','set_offline(True)','hgViewer?.ready']:
            self.assertIn(check,text)
