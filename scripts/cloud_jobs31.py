"""Git push intake and versioned public Blender jobs; TEST 30 is not executed."""
import argparse
import json
import os
import html
import hashlib
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.cloud_jobs31 import discover, run_job, write_json, WorkerError


def dashboard(output, summary):
    rows = []
    for job in summary['results']:
        fields = [job['job_id'], str(job['revision']), job['status'], str(job.get('progress_percent', 0)) + '%', job.get('error') or '']
        cells = ''.join('<td>' + html.escape(s) + '</td>' for s in fields)
        links = ''
        if job['status'] == 'NEEDS_REVIEW':
            prefix = job['job_id'] + '/' + job['version'] + '/published/'
            links = ' '.join('<a href="' + html.escape(prefix + filename, quote=True) + '">' + label + '</a>'
                             for filename, label in [('hg_scene.blend', 'BLEND'), ('hg_scene.glb', 'GLB'), ('qa_report.json', 'QA')])
        rows.append('<tr>' + cells + '<td>' + links + '</td></tr>')
    (output / 'index.html').write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>TEST 31</title><style>body{font:16px system-ui;margin:24px}td,th{padding:10px;border:1px solid #aaa}table{border-collapse:collapse}main{overflow:auto}</style>'
        '<h1>TEST 31 — công việc mẫu công khai</h1><p>TEST 30: CẦN XÁC NHẬN. Kết quả dựng chưa được nghiệm thu. Không render.</p>'
        '<main><table><tr><th>Công việc</th><th>Phiên bản yêu cầu</th><th>Trạng thái</th><th>Tiến độ</th><th>Lỗi</th><th>File đã kiểm định</th></tr>'
        + ''.join(rows) + '</table></main></html>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--before', default='')
    parser.add_argument('--commit', required=True)
    parser.add_argument('--request-id', default='')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    output, work = args.output.resolve(), args.work.resolve()
    if output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError('Uploaded output and unverified workspace must be separate')
    output.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    summary = dict(test='TEST 31', status='RUNNING', results=[], test30_status='CẦN XÁC NHẬN',
                   render_executed=False, paid_api_called=False, request_mode='public catalog only')
    try:
        actual_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        if actual_commit != args.commit:
            raise ValueError('Execution commit must match checkout HEAD')
        selected = discover(args.before, args.commit, args.request_id)
        for request in selected:
            blob = subprocess.run(['git', 'show', args.commit + ':' + request['request_path']], cwd=ROOT,
                                  capture_output=True, check=True).stdout
            if hashlib.sha256(blob).hexdigest() != request['request_sha256']:
                raise ValueError('Request must match its immutable Git snapshot')
        write_json(output / 'intake.json', dict(status='ACCEPTED', commit=args.commit, requests=selected))
        for request in selected:
            try:
                state = run_job(request, output, work, args.commit, args.run_id, args.attempt)
            except WorkerError as exc:
                state = dict(job_id=request['job_id'], revision=request['revision'], status='BLOCKED_ATTEMPT',
                             version=None, error=exc.code, progress_percent=0)
            summary['results'].append(state)
            expected_failure = request['sample'] == 'qa-failure-demo'
            acceptable = state['status'] == ('FAILED' if expected_failure else 'NEEDS_REVIEW')
            if expected_failure:
                acceptable = acceptable and state['error'] == 'QA_FAILED'
            state['expected_negative_fixture'] = expected_failure
            state['test_expectation_met'] = acceptable
            write_json(output / 'batch.json', summary)
            dashboard(output, summary)
            if os.environ.get('GITHUB_ACTIONS'):
                compact = dict(job=state['job_id'], revision=state['revision'], version=state['version'],
                               status=state['status'], error=state['error'], progress=state['progress_percent'],
                               expected_negative_fixture=expected_failure, expectation_met=acceptable)
                print('::notice title=TEST31 actual job::' + json.dumps(compact, ensure_ascii=False), flush=True)
        summary['status'] = ('NO_NEW_REQUESTS' if not selected else
                             'PASS_PUBLIC_JOB_TRIAL' if all(r['test_expectation_met'] for r in summary['results']) else 'FAILED')
    except Exception as exc:
        # Never copy an invalid request, exception payload, or unverified model.
        summary.update(status='FAILED', error_class=type(exc).__name__)
        if os.environ.get('GITHUB_ACTIONS'):
            print('::error title=TEST31 intake or worker::Request rejected or attempt interrupted; inspect safe ledger', flush=True)
        raise
    finally:
        write_json(output / 'batch.json', summary)
        report = ('# TEST 31 — công việc Blender công khai\n\n'
                  'Mẫu tham số công khai, không phải kết quả nhận diện ảnh. TEST 30 giữ '
                  'CẦN XÁC NHẬN, không chạy lại. FAILED ở mẫu âm không có model được công bố.\n\n'
                  '```json\n' + json.dumps(summary, ensure_ascii=False, indent=2) + '\n```\n')
        (output / 'REPORT_TEST31_VI.md').write_text(report)
        dashboard(output, summary)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream: stream.write(report)
    if summary['status'] == 'FAILED':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
