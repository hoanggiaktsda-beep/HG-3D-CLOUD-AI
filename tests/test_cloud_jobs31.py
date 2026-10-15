"""TEST 31 only: protocol fixtures + real Blender/timeout, not TEST 30."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from hgcloud.cloud_jobs31 import request_at, discover, run_job, event, command, WorkerError, manifest_valid

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'a' * 40


class CloudJobs31Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'outputs', prefix='test31-regression-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.requests = self.root / 'jobs/public'
        self.requests.mkdir(parents=True)

    def request(self, ident='demo', revision=1, sample='console-demo'):
        folder = self.requests / ident
        folder.mkdir(exist_ok=True)
        path = folder / f'v{revision:04}.json'
        path.write_text(json.dumps(dict(schema_version=1, job_id=ident, revision=revision,
                                       parent_revision=revision - 1, sample=sample)))
        return path

    def run_job(self, request, attempt=1):
        return run_job(request_at(request, self.requests), self.root / 'ledger', self.root / 'work', COMMIT, 'local-regression', attempt)

    def test_public_contract_rejects_arbitrary_input_and_missing_parent(self):
        path = self.request()
        self.assertEqual(request_at(path, self.requests)['sample'], 'console-demo')
        data = json.loads(path.read_text())
        path.write_text(json.dumps(dict(data, image_url='https://example.invalid/private.png')))
        with self.assertRaises(ValueError): request_at(path, self.requests)
        path.write_text(json.dumps(dict(data, sample='not-approved')))
        with self.assertRaises(ValueError): request_at(path, self.requests)
        path = self.request('orphan', 2)
        with self.assertRaises(ValueError): request_at(path, self.requests)
        path = self.request('linked')
        link = path.with_name('v0002.json')
        link.symlink_to(path)
        with self.assertRaises(ValueError): request_at(link, self.requests)

    def test_push_intake_is_immutable_bounded_and_dispatch_is_not_a_path(self):
        path = self.request()
        result = subprocess.CompletedProcess([], 0, 'A\tjobs/public/demo/v0001.json\n', '')
        with patch('hgcloud.cloud_jobs31.subprocess.run', return_value=result):
            self.assertEqual(len(discover('b' * 40, COMMIT, root=self.root)), 1)
        for status in ['M', 'D', 'R']:
            result.stdout = status + '\tjobs/public/demo/v0001.json\n'
            with patch('hgcloud.cloud_jobs31.subprocess.run', return_value=result), self.assertRaises(ValueError):
                discover('b' * 40, COMMIT, root=self.root)
        result.stdout = 'A\tjobs/public/demo/v0001.json\n' * 6
        with patch('hgcloud.cloud_jobs31.subprocess.run', return_value=result), self.assertRaises(ValueError):
            discover('b' * 40, COMMIT, root=self.root)
        with self.assertRaises(ValueError): discover('', COMMIT, '../private', self.root)
        self.assertEqual(discover('', COMMIT, 'demo/v0001', self.root)[0]['job_id'], 'demo')

    def test_progress_is_monotonic_and_terminal_states_cannot_restart(self):
        folder = self.root / 'state'
        folder.mkdir()
        state = dict(job_id='demo', revision=1, version='fixture')
        for status, progress in [('QUEUED', 0), ('BUILDING', 20), ('VERIFYING', 65), ('PUBLISHING', 90), ('NEEDS_REVIEW', 100)]:
            event(folder, state, status, progress)
        self.assertEqual(len((folder / 'events.jsonl').read_text().splitlines()), 5)
        with self.assertRaises(ValueError): event(folder, state, 'BUILDING', 20)
        with self.assertRaises(ValueError): event(folder, {}, 'NEEDS_REVIEW', 100)

    def test_actual_process_timeout_kills_worker(self):
        with self.assertRaises(WorkerError) as caught:
            command([sys.executable, '-c', 'import time; time.sleep(10)'], self.root / 'timeout.log', .05)
        self.assertEqual(caught.exception.code, 'WORKER_TIMEOUT')

    @unittest.skipUnless(shutil.which('blender'), 'Real Blender required')
    def test_actual_blender_revision_retry_integrity_and_idempotent_attempt(self):
        path = self.request()
        first = self.run_job(path)
        self.assertEqual(first['status'], 'NEEDS_REVIEW')
        self.assertFalse(first['final_approved'])
        self.assertEqual(first['test30_status'], 'CẦN XÁC NHẬN')
        folder = self.root / 'ledger/demo' / first['version']
        self.assertTrue(manifest_valid(folder / 'published'))
        log = (folder / 'blender.log').stat().st_mtime_ns
        self.assertEqual(self.run_job(path)['version'], first['version'])
        self.assertEqual((folder / 'blender.log').stat().st_mtime_ns, log)
        revision2 = self.run_job(self.request(revision=2))
        self.assertNotEqual(first['version'], revision2['version'])
        self.assertEqual(revision2['parent_revision'], 1)
        self.assertEqual(revision2['parent_request_sha256'], first['request_sha256'])
        glb = folder / 'published/hg_scene.glb'
        glb.write_bytes(b'changed-public-test-output')
        with self.assertRaises(WorkerError): self.run_job(path)
        (folder / 'published/manifest.json').write_text('broken manifest fixture')
        with self.assertRaises(WorkerError) as corrupt: self.run_job(path)
        self.assertEqual(corrupt.exception.code, 'ARTIFACT_INTEGRITY_FAILED')
        retry = self.run_job(path, attempt=2)
        self.assertEqual(retry['status'], 'NEEDS_REVIEW')
        self.assertNotEqual(first['version'], retry['version'])
        self.assertEqual(glb.read_bytes(), b'changed-public-test-output')

    @unittest.skipUnless(shutil.which('blender'), 'Real Blender required')
    def test_real_qa_failure_does_not_publish_and_next_job_runs(self):
        bad = self.run_job(self.request('bad', sample='qa-failure-demo'))
        self.assertEqual(bad['status'], 'FAILED')
        self.assertEqual(bad['error'], 'QA_FAILED')
        folder = self.root / 'ledger/bad' / bad['version']
        self.assertFalse((folder / 'published').exists())
        qa = json.loads((folder / 'failure_qa.json').read_text())
        self.assertEqual(qa['geometry_status'], 'QA_FAILED')
        self.assertGreater(abs(qa['geometry_measurements'][0]['error_mm'][0]), 99)
        self.assertEqual(self.run_job(self.request('after-failure'))['status'], 'NEEDS_REVIEW')

    def test_interrupted_attempt_is_not_reported_successful(self):
        path = self.request()
        version = f'r0001-{COMMIT[:12]}-local-regression-a1'
        folder = self.root / 'ledger/demo' / version
        folder.mkdir(parents=True)
        request = request_at(path, self.requests)
        (folder / 'state.json').write_text(json.dumps(dict(status='BUILDING', request_sha256=request['request_sha256'], commit=COMMIT)))
        with self.assertRaises(WorkerError) as caught: self.run_job(path)
        self.assertEqual(caught.exception.code, 'INCOMPLETE_ATTEMPT_USE_NEW_RUN_ATTEMPT')


if __name__ == '__main__': unittest.main()
