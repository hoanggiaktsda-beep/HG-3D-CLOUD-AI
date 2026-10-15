"""Public-demo-only Actions jobs. No customer uploads, Python payloads or rendering."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
from datetime import datetime, timezone
from .vision import ROLES

ROOT = Path(__file__).resolve().parents[1]
REQUESTS = ROOT / 'jobs/public'
SAMPLE_SHA = '6682694b2a47adac9392ec58bca84b1e083554cc3de3c4fb883c09e14ad7b49e'
SAMPLES = {'console-demo', 'qa-failure-demo'}
TERMINAL = {'NEEDS_REVIEW', 'FAILED'}
TRANSITIONS = {'QUEUED': {'BUILDING', 'FAILED'}, 'BUILDING': {'VERIFYING', 'FAILED'},
               'VERIFYING': {'PUBLISHING', 'FAILED'}, 'PUBLISHING': {'NEEDS_REVIEW', 'FAILED'}}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    os.replace(temporary, path)


def request_at(path, root=REQUESTS):
    path, root = Path(path), Path(root).resolve()
    relative = path.absolute().relative_to(root)
    if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise ValueError('Symlink requests are forbidden')
    if not path.resolve().is_relative_to(root) or path.stat().st_size > 4096:
        raise ValueError('Request outside public catalog or too large')
    data = json.loads(path.read_text())
    if set(data) != {'schema_version', 'job_id', 'revision', 'parent_revision', 'sample'}:
        raise ValueError('Only public catalog fields are allowed; no URLs, images, paths or code')
    ident, rev = data['job_id'], data['revision']
    if type(data['schema_version']) is not int or data['schema_version'] != 1 or not isinstance(ident, str) or not re.fullmatch('[a-z][a-z0-9-]{0,47}', ident):
        raise ValueError('Invalid public job identity')
    if type(rev) is not int or not 1 <= rev <= 100 or type(data['parent_revision']) is not int or data['parent_revision'] != rev - 1:
        raise ValueError('Revisions must be sequential integers')
    if not isinstance(data['sample'], str) or data['sample'] not in SAMPLES:
        raise ValueError('Unapproved sample')
    if relative.as_posix() != f'{ident}/v{rev:04}.json':
        raise ValueError('Request path must match identity and revision')
    if rev > 1:
        parent = root / ident / f'v{rev - 1:04}.json'
        if not parent.is_file() or parent.is_symlink():
            raise ValueError('Parent revision missing')
        previous = json.loads(parent.read_text())
        if previous.get('job_id') != ident or previous.get('revision') != rev - 1:
            raise ValueError('Parent revision mismatch')
    return dict(data, request_sha256=digest(path), parent_request_sha256=digest(parent) if rev > 1 else None,
                request_path='jobs/public/' + relative.as_posix())


def discover(before, commit, request_id='', root=ROOT):
    root = Path(root)
    if not re.fullmatch('[a-f0-9]{40}', commit):
        raise ValueError('A full immutable commit is required')
    if request_id:
        if not re.fullmatch('[a-z][a-z0-9-]{0,47}/v[0-9]{4}', request_id):
            raise ValueError('Invalid dispatch request ID')
        paths = [root / 'jobs/public' / (request_id + '.json')]
    else:
        if not re.fullmatch('[a-f0-9]{40}', before) or before == '0' * 40:
            raise ValueError('Valid push base required; use explicit dispatch for initial repository')
        result = subprocess.run(['git', 'diff', '--name-status', '--no-renames', before, commit, '--', 'jobs/public/'],
                                cwd=root, capture_output=True, text=True, check=True)
        paths = []
        for line in result.stdout.splitlines():
            status, name = line.split('\t')
            if status != 'A' or not name.endswith('.json'):
                raise ValueError('Public requests are immutable: append a new revision; do not edit/delete old requests')
            paths.append(root / name)
    if len(paths) > 5:
        raise ValueError('Maximum five new public jobs per run')
    return [request_at(p, root / 'jobs/public') for p in sorted(paths)]


class WorkerError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def command(args, log, timeout):
    with Path(log).open('ab') as output:
        try:
            process = subprocess.Popen(list(map(str, args)), cwd=ROOT, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        except FileNotFoundError as exc:
            raise WorkerError('BLENDER_UNAVAILABLE') from exc
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise WorkerError('WORKER_TIMEOUT') from exc
        if code:
            raise WorkerError('BLENDER_EXIT')


def event(folder, state, status, progress, error=None):
    previous = state.get('status')
    if not previous and status != 'QUEUED' or not 0 <= progress <= 100 or progress < state.get('progress_percent', 0):
        raise ValueError('Invalid/nonmonotonic progress')
    if previous and status not in TRANSITIONS.get(previous, set()):
        raise ValueError('Invalid job state transition')
    state.update(status=status, progress_percent=progress, error=error,
                 updated_utc=datetime.now(timezone.utc).isoformat())
    write_json(folder / 'state.json', state)
    entry = dict(status=status, progress_percent=progress, error=error, time=state['updated_utc'])
    with (folder / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(json.dumps(dict(job_id=state['job_id'], revision=state['revision'], version=state['version'], **entry)), flush=True)


def manifest_valid(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    expected = {'hg_scene.blend', 'hg_scene.glb', 'qa_report.json', 'interchange_qa.json', 'scene.json'}
    return set(manifest) == expected and all((folder / name).is_file() and not (folder / name).is_symlink()
           and digest(folder / name) == item['sha256'] and (folder / name).stat().st_size == item['bytes']
           for name, item in manifest.items())


def run_job(request, output, work, commit, run_id, attempt, timeout=120):
    if not re.fullmatch('[a-z][a-z0-9-]{0,47}', request['job_id']) or type(request['revision']) is not int or not 1 <= request['revision'] <= 100:
        raise ValueError('Invalid job identity')
    if not re.fullmatch('[a-f0-9]{40}', commit) or not re.fullmatch('[A-Za-z0-9-]{1,50}', str(run_id)) or type(attempt) is not int or not 1 <= attempt <= 100:
        raise ValueError('Invalid immutable execution identity')
    version = f'r{request["revision"]:04}-{commit[:12]}-{run_id}-a{attempt}'
    folder = Path(output) / request['job_id'] / version
    state = dict(job_id=request['job_id'], revision=request['revision'], parent_revision=request['parent_revision'],
                 sample=request['sample'], request_sha256=request['request_sha256'], commit=commit,
                 parent_request_sha256=request.get('parent_request_sha256'), public_sample_sha256=SAMPLE_SHA,
                 run_id=str(run_id), run_attempt=attempt, version=version, roles=ROLES,
                 run_url=f'https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/{run_id}' if str(run_id).isdigit() else None,
                 request_source_url=f'https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/blob/{commit}/{request["request_path"]}',
                 test30_status='CẦN XÁC NHẬN', final_approved=False, render_executed=False,
                 automatic_vision_executed=False, input_kind='public procedural demo; not image recognition')
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        saved = json.loads((folder / 'state.json').read_text())
        if saved.get('request_sha256') != request['request_sha256'] or saved.get('commit') != commit or saved.get('status') not in TERMINAL:
            raise WorkerError('INCOMPLETE_ATTEMPT_USE_NEW_RUN_ATTEMPT')
        if saved['status'] == 'NEEDS_REVIEW' and not manifest_valid(folder / 'published'):
            raise WorkerError('ARTIFACT_INTEGRITY_FAILED')
        return saved
    event(folder, state, 'QUEUED', 0)
    build = Path(work) / request['job_id'] / version
    try:
        if request['sample'] not in SAMPLES:
            raise WorkerError('UNAPPROVED_SAMPLE')
        sample = ROOT / 'examples/product_console.json'
        if digest(sample) != SAMPLE_SHA:
            raise WorkerError('PUBLIC_SAMPLE_CHANGED')
        build.mkdir(parents=True, exist_ok=False)
        scene_path = build / 'scene.json'
        shutil.copyfile(sample, scene_path)
        model_dir = build / 'build'
        event(folder, state, 'BUILDING', 20)
        blender = ['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python']
        command([*blender, ROOT / 'scripts/blender_build.py', '--', scene_path, model_dir], folder / 'blender.log', timeout)
        event(folder, state, 'VERIFYING', 65)
        verify_scene = scene_path
        if request['sample'] == 'qa-failure-demo':
            # Deliberately incorrect EXPECTATION for a public negative test.
            # Blender still builds and measures the real original geometry.
            data = json.loads(scene_path.read_text())
            data['objects'][0]['size_mm'][0] += 100
            verify_scene = build / 'negative-test-expectation.json'
            write_json(verify_scene, data)
        command([*blender, ROOT / 'scripts/verify_blender.py', '--', verify_scene, model_dir], folder / 'blender.log', timeout)
        qa = json.loads((model_dir / 'qa_report.json').read_text())
        if qa.get('geometry_status') != 'PASS' or qa['blender_details']['glb_error']:
            raise WorkerError('QA_FAILED')
        command([*blender, ROOT / 'scripts/blender_job_interchange.py', '--', model_dir], folder / 'blender.log', timeout)
        raw = (model_dir / 'hg_scene.glb').read_bytes()
        if struct.unpack('<4sII', raw[:12]) != (b'glTF', 2, len(raw)):
            raise WorkerError('GLB_INVALID')
        qa.update(status='NEEDS_REVIEW', test30_status='CẦN XÁC NHẬN', final_approved=False)
        write_json(model_dir / 'qa_report.json', qa)
        event(folder, state, 'PUBLISHING', 90)
        # Stage outside uploaded output; rename atomically only after validation.
        staging = build / 'validated'
        staging.mkdir()
        for name in ['hg_scene.blend', 'hg_scene.glb', 'qa_report.json', 'interchange_qa.json']:
            shutil.copyfile(model_dir / name, staging / name)
        shutil.copyfile(scene_path, staging / 'scene.json')
        manifest = {p.name: dict(bytes=p.stat().st_size, sha256=digest(p)) for p in staging.iterdir()}
        write_json(staging / 'manifest.json', manifest)
        if not manifest_valid(staging):
            raise WorkerError('ARTIFACT_INTEGRITY_FAILED')
        os.replace(staging, folder / 'published')
        event(folder, state, 'NEEDS_REVIEW', 100)
    except Exception as exc:
        error = exc.code if isinstance(exc, WorkerError) else 'WORKER_INTERNAL_ERROR'
        qa_path = build / 'build/qa_report.json'
        if qa_path.is_file():
            try:
                diagnostic = json.loads(qa_path.read_text())
                write_json(folder / 'failure_qa.json', diagnostic)
                if diagnostic.get('geometry_status') == 'QA_FAILED':
                    error = 'QA_FAILED'
            except (ValueError, OSError):
                error = 'QA_REPORT_INVALID'
        if (folder / 'published').exists():
            # A crash during final transition must not leave downloadable outputs.
            os.replace(folder / 'published', build / 'unpublished-after-failure')
        event(folder, state, 'FAILED', state['progress_percent'], error)
    return state
