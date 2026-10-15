"""Public-only real VLM experiment. No supplied response files, secrets or renders."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.intake import receive, compile_scene
from hgcloud.core import SceneError
from hgcloud.local_vision import LocalCPUVision
from cloud_worker_sample import SOURCE_URL, verified_source

MODEL_ID = 'HuggingFaceTB/SmolVLM-256M-Instruct'
# Resolve to an immutable commit before downloading and record it in every result.
MODEL_REVISION = 'main'


def notice(title, message, error=False):
    if os.environ.get('GITHUB_ACTIONS'):
        message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::{"error" if error else "notice"} title={title}::{message}', flush=True)


def download(url, limit=20 * 1024 * 1024):
    request = urllib.request.Request(url, headers={'User-Agent': 'HG3D-Public-Research/1.0 (https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI)'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Public source exceeds limit')
    return data


def public_sources(out):
    from PIL import Image
    sources = []
    pdf = out / 'public-atfab.pdf'
    pdf.write_bytes(verified_source(download(SOURCE_URL)))
    for page in [1, 3, 6]:
        subprocess.run(['pdftoppm', '-scale-to', '1800', '-f', str(page), '-l', str(page), '-singlefile', '-png', str(pdf), str(out / f'atfab-{page}')], check=True, timeout=60)
    # Crop away labels; this sample tests actual visual inference of a perspective drawing.
    with Image.open(out / 'atfab-1.png') as image:
        image.crop((100, 130, 660, 880)).save(out / 'public-perspective.png')
    for name, kind, file, description in [
            ('perspective', 'product_photo', 'public-perspective.png', 'Perspective line drawing, NOT a real product photograph'),
            ('drawing', 'technical_drawing', 'atfab-3.png', 'Public dimensioned furniture drawing')]:
        sources.append(dict(name=name, input_type=kind, file=file, description=description,
                            url=SOURCE_URL, license='CC BY-NC-SA 3.0, PDF page 6', author='AtFAB / Filson and Rohrbacher 2013'))
    # Optional independent photos/layout: only explicitly permitted licenses, no customer upload.
    for name, category, kind in [('interior', 'Living rooms', 'interior_photo'),
                                 ('product', 'Chairs', 'product_photo'),
                                 ('layout', 'Floor plans of houses', 'layout')]:
        try:
            query = dict(action='query', generator='categorymembers', gcmtitle='Category:' + category,
                         gcmtype='file', gcmlimit='15', prop='imageinfo', iiprop='url|extmetadata', iiurlwidth='768', format='json')
            payload = json.loads(download('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(query)))
            found = False
            for page in payload.get('query', {}).get('pages', {}).values():
                info = page.get('imageinfo', [{}])[0]
                metadata = info.get('extmetadata', {})
                license_name = metadata.get('LicenseShortName', {}).get('value', '')
                if license_name not in {'CC0', 'Public domain', 'CC BY 4.0', 'CC BY-SA 4.0', 'CC BY 3.0', 'CC BY-SA 3.0'}:
                    continue
                url = info.get('thumburl', info.get('url', ''))
                if not url.startswith('https://upload.wikimedia.org/') or not re.search(r'\.(?:jpe?g|png)(?:\?|$)', url, re.I):
                    continue
                data = download(url)
                file = out / f'commons-{name}.png'
                import io
                with Image.open(io.BytesIO(data)) as image:
                    image.convert('RGB').save(file)
                sources.append(dict(name=name, input_type=kind, file=file.name, description=page['title'],
                                    url=info['descriptionurl'], download_url=url, license=license_name,
                                    license_url=metadata.get('LicenseUrl', {}).get('value', ''),
                                    author=html.unescape(re.sub('<[^>]+>', '', metadata.get('Artist', {}).get('value', 'Unknown')))))
                found = True
                break
            if not found:
                raise ValueError('No compatible licensed raster in category; no replacement fixture')
        except Exception as exc:
            sources.append(dict(name=name, input_type=kind, status='SOURCE_UNAVAILABLE', reason=str(exc)))
    (out / 'public_sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2))
    return sources


def load_model(cache):
    from huggingface_hub import HfApi, snapshot_download
    info = HfApi().model_info(MODEL_ID, revision=MODEL_REVISION, files_metadata=True)
    license_name = (info.card_data.to_dict() if info.card_data else {}).get('license')
    if license_name != 'apache-2.0' or info.private or info.gated:
        raise ValueError('Expected public ungated Apache-2.0 model; refuse changed terms')
    files = [entry for entry in info.siblings if entry.rfilename.endswith('.safetensors')]
    if not files or any(entry.size is None for entry in files) or sum(entry.size for entry in files) > 2_000_000_000:
        raise ValueError('Model weights missing or CPU download budget exceeded')
    metadata = dict(model_id=MODEL_ID, revision=info.sha, license=license_name,
                    weights_bytes=sum(entry.size for entry in files), device='cpu', remote_code=False)
    notice('Real VLM model provenance', json.dumps(metadata))
    snapshot = Path(snapshot_download(MODEL_ID, revision=info.sha, cache_dir=str(cache),
                                     allow_patterns=['*.json', '*.safetensors', 'tokenizer.model', 'vocab.*', 'merges.txt']))
    metadata['safetensors_sha256'] = {str(p.relative_to(snapshot)): hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.rglob('*.safetensors')}
    return LocalCPUVision(snapshot, metadata), metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-cache', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status='STARTED', live_model_executed=False, results=[])
    try:
        sources = public_sources(out)
        model, metadata = load_model(args.model_cache.resolve())
        (out / 'model_provenance.json').write_text(json.dumps(metadata, indent=2))
        for source in sources:
            if source.get('status') == 'SOURCE_UNAVAILABLE':
                state['results'].append(source)
                continue
            job = out / ('job-' + source['name'])
            receive(out / source['file'], source['input_type'], job)
            result = model.analyze(job / 'intake.json')
            result['public_source'] = source
            (job / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
            if result['observations']:
                observations = job / 'observations.json'
                observations.write_text(json.dumps(result['observations'], ensure_ascii=False, indent=2))
                try:
                    compile_scene(job / 'intake.json', observations)
                except SceneError as exc:
                    result['build_gate'] = str(exc)
                else:
                    raise RuntimeError('Unreviewed VLM proposal unexpectedly passed build gate')
            else:
                result['build_gate'] = 'BLOCKED: invalid geometry JSON; no fallback objects'
            state['live_model_executed'] = True
            summary = dict(name=source['name'], status=result['status'], caption=result['caption'],
                           raw_geometry_response=result['raw_geometry_response'], reason=result.get('reason'),
                           build_gate=result['build_gate'], inference_seconds=result['execution']['inference_seconds'],
                           generated_tokens=result['execution']['generated_tokens'], build_allowed=False)
            state['results'].append(summary)
            notice('Actual public VLM result - ' + source['name'], json.dumps(summary, ensure_ascii=False))
        state['status'] = 'EXPERIMENT_COMPLETED_NOT_ACCEPTED'
    except Exception as exc:
        state.update(status='FAILED', error=str(exc))
        (out / 'failure.log').write_text(traceback.format_exc())
        notice('Public VLM failed - not recognition success', traceback.format_exc()[-8000:], error=True)
        raise
    finally:
        (out / 'experiment.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
        report = ('# Thử nghiệm AI thị giác CPU thật\n\n'
                  'Không phải nghiệm thu nhận diện hoặc dựng tự động. Không render. Không API trả phí.\n\n'
                  'Mô hình sinh caption và đề xuất JSON từ pixel; không có phản hồi fixture/replay. '
                  'Mọi số đo/vị trí AI đề xuất đều CẦN XÁC NHẬN. Chưa có BLEND/GLB từ đề xuất chưa duyệt.\n\n'
                  'Ảnh có thể đọc được không chứng minh hình học chính xác. Phải đối chiếu nguồn độc lập '
                  'trước khi chuyển observations sang compile_scene và Blender Cloud Worker hiện có.\n\n'
                  '18 vai trò là trách nhiệm kiểm tra, không phải 18 mô hình đã thực thi.\n\n'
                  '```json\n' + json.dumps(state, ensure_ascii=False, indent=2) + '\n```\n')
        (out / 'REPORT_VI.md').write_text(report)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
                summary.write(report)


if __name__ == '__main__':
    main()
