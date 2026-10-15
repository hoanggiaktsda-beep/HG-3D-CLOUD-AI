"""Real Qwen + independent OCR -> evidence gate -> Blender; public fixed inputs only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.assembly_evidence import agree_calibration, view_and_part_candidates
from hgcloud.core import SceneError
from hgcloud.cut_layout import extract_layout
from hgcloud.cut_layout_qa import verify_projection
from hgcloud.quantized_vision import QuantizedCPUVision
from hgcloud.vision import ROLES
from scripts.public_vision_trial import download, notice

MODEL = 'Qwen/Qwen2-VL-2B-Instruct'
REVISION = '895c3a49bc3fa70a340399125c650a463535e71c'
TRANSCRIBE = 'Transcribe all printed text faithfully, including numbers, unit symbols, color legend and table rows. Use original words. Do not add explanations or guess missing words.'
VIEW = 'Describe the drawing view and the visible or labelled furniture parts. State any explicitly dimensioned positions. Do not guess dimensions, hidden parts or assembled coordinates.'


def read_pixels(provider, image, purpose):
    """Bounded live retry for empty/chat-role output, before any OCR is available."""
    prompts = [VIEW if purpose == 'view' else TRANSCRIBE,
               'Read all text in this image. Preserve numbers and units. Do not guess.']
    attempts = []
    for prompt in prompts:
        started = time.monotonic()
        text, tokens = provider.generate(image, prompt, 128 if purpose == 'view' else 256)
        attempts.append(dict(prompt=prompt, text=text, generated_tokens=tokens,
                             inference_seconds=time.monotonic() - started))
        if len(''.join(c for c in text if c.isalnum())) >= 10 and text.strip().lower() not in {'system', 'assistant', 'user'}:
            break
    return attempts[-1]['text'], attempts

# Source selection and supervised crop locations ONLY: no design sizes, answers,
# part counts, material thickness, colors, contours or geometry JSON are supplied.
CASES = [
    dict(id='desk', folder='OD-51380-Desk-1.1.0', code='OD-51380',
         sha256='6ebbf999eae55082711585656d5476873baa3745861af496b0bce8ef33a5759e',
         author='zerozero', license='CC BY 4.0 (source LICENSE.txt)', pages=[1],
         tasks=[('view', 1, [25, 40, 760, 1050])], layout_page=None),
    dict(id='chair', folder='OD-51381-5-To-30-Minute-Chair-1.0.0', code='OD-51381',
         sha256='e295e6496d2b5dc314175afc678bf7b0aa61d984dc52b7d53e50c4d602441445',
         author='AtFAB / Filson and Rohrbacher 2013', license='CC BY-NC-SA 3.0 (PDF page 7)', pages=[4, 5, 6, 7],
         tasks=[('cut_context', 4, [30, 400, 520, 740]), ('material', 6, [30, 600, 445, 1020]),
                ('parts_table', 5, [30, 1110, 445, 1340]), ('view', 5, [490, 420, 1220, 1550])], layout_page=4),
    dict(id='table', folder='OD-51383-One-To-Several-Table-1.0.0', code='OD-51383',
         sha256='97775bcc2b30a768d18170d49118afbd9020181c45cafd7013ddbf2925fc0d6a',
         author='AtFAB / Filson and Rohrbacher 2011', license='CC BY-NC-SA 3.0 (PDF page 6)', pages=[4, 6],
         tasks=[('cut_context', 4, [25, 350, 560, 680])], layout_page=4),
]


def load_provider(cache):
    from huggingface_hub import HfApi, snapshot_download
    info = HfApi().model_info(MODEL, revision=REVISION, files_metadata=True)
    if info.private or info.gated or info.card_data.to_dict().get('license') != 'apache-2.0':
        raise ValueError('Expected public ungated Apache-2.0 model')
    weights = [entry for entry in info.siblings if entry.rfilename.endswith('.safetensors')]
    if not weights or any(entry.size is None for entry in weights) or sum(entry.size for entry in weights) > 6_000_000_000:
        raise ValueError('Model exceeds free CPU download budget')
    metadata = dict(model_id=MODEL, revision=info.sha, license='apache-2.0', device='cpu', remote_code=False)
    snapshot = Path(snapshot_download(MODEL, revision=info.sha, cache_dir=str(cache),
                                     allow_patterns=['*.json', '*.safetensors', 'tokenizer.model', 'vocab.*', 'merges.txt']))
    metadata['weights_sha256'] = {str(p.relative_to(snapshot)): hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.rglob('*.safetensors')}
    return QuantizedCPUVision(snapshot, metadata), metadata


def run_blender(script, args, log):
    command = ['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(ROOT / 'scripts' / script), '--', *map(str, args)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=240)
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        notice('Blender actual failure', (result.stdout + result.stderr)[-7000:], error=True)
    result.check_returncode()


def main():
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-cache', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status='STARTED', results=[], roles=ROLES, render_executed=False, website_connected=False)
    try:
        provider, metadata = load_provider(args.model_cache.resolve())
        (out / 'model_provenance.json').write_text(json.dumps(metadata, indent=2))
        for case in CASES:
            job = out / case['id']
            job.mkdir()
            base = 'https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/' + case['folder'] + '/'
            data = download(base + case['code'] + '-Assembly-Guide.pdf')
            if hashlib.sha256(data).hexdigest() != case['sha256']:
                raise ValueError('Public drawing content changed; stop for review')
            pdf = job / 'public-source.pdf'
            pdf.write_bytes(data)
            (job / 'LICENSE-source.txt').write_bytes(download(base + 'LICENSE.txt'))
            source_info = dict(url=base + case['code'] + '-Assembly-Guide.pdf', sha256=case['sha256'],
                               author=case['author'], license=case['license'], supervised_crops=True,
                               answers_supplied_to_model=False, original_geometry_json_used=False)
            (job / 'source.json').write_text(json.dumps(source_info, indent=2))
            pages = {}
            for page in case['pages']:
                prefix = job / ('page-' + str(page))
                result = subprocess.run(['pdftoppm', '-scale-to', '4800', '-f', str(page), '-l', str(page), '-singlefile', '-png', str(pdf), str(prefix)],
                                        capture_output=True, text=True, timeout=60)
                (job / ('raster-' + str(page) + '.log')).write_text(result.stderr)
                result.check_returncode()
                pages[page] = prefix.with_suffix('.png')
            records = []
            for purpose, page, box in case['tasks']:
                image_path = job / (purpose + '.png')
                with Image.open(pages[page]) as original:
                    scale = original.height / 1800
                    original.crop(tuple(round(value * scale) for value in box)).convert('RGB').save(image_path)
                digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
                with Image.open(image_path) as image:
                    # Actual model call first. No OCR, answers or geometry passed to it.
                    ai_text, attempts = read_pixels(provider, image.convert('RGB'), purpose)
                elapsed = sum(a['inference_seconds'] for a in attempts)
                tokens = sum(a['generated_tokens'] for a in attempts)
                result = subprocess.run(['tesseract', str(image_path), 'stdout', '--psm', '6'], capture_output=True, text=True, timeout=60, check=True)
                record = dict(purpose=purpose, page=page, supervised_roi_at_1800=box,
                              image_path=str(image_path), image_sha256=digest, document_sha256=case['sha256'],
                              ai_text=ai_text, ai_attempts=attempts, ocr_text=result.stdout, ocr_image_sha256=digest,
                              execution=dict(live_model_executed=True, backend='qwen2vl_cpu_live', model_revision=REVISION,
                                             image_sha256=digest, generated_tokens=tokens, inference_seconds=elapsed),
                              observations=view_and_part_candidates(ai_text, result.stdout))
                records.append(record)
                (job / 'readings.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
                notice('Actual independent reading - ' + case['id'] + '-' + purpose,
                       json.dumps(dict(ai_text=ai_text, ai_attempts=attempts, ocr_text=result.stdout, seconds=elapsed, observations=record['observations']), ensure_ascii=False))
            summary = dict(case=case['id'], source=source_info, live_model_executed=True, status='CẦN XÁC NHẬN',
                           outputs_created=False, assembly_allowed=False)
            try:
                calibration = agree_calibration(records, case['sha256'])
                layout = extract_layout(pages[case['layout_page']], calibration)
                layout['document_sha256'] = case['sha256']
                layout['license'] = case['license']
                layout['attribution'] = case['author']
                layout['source_url'] = source_info['url']
                layout['vision_evidence'] = records
                layout['roles'] = ROLES
                spec_path = job / 'cut_layout.json'
                spec_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2))
                run_blender('blender_cut_layout.py', [spec_path, job / 'build'], job / 'blender.log')
                qa = json.loads((job / 'build/part_qa.json').read_text())
                qa['source_projection'] = verify_projection(layout, qa)
                qa['source_warnings'] = layout['source_warnings']
                (job / 'build/part_qa.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2))
                glb = (job / 'build/cut_layout.glb').read_bytes()
                if struct.unpack('<4sII', glb[:12]) != (b'glTF', 2, len(glb)):
                    raise RuntimeError('Invalid GLB file')
                summary.update(status='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW', outputs_created=True,
                               parts=len(layout['parts']), inside_cuts=sum(len(p['voids_mm']) for p in layout['parts']),
                               drill_markers=qa['drill_markers'], physical_drill_bores=0,
                               min_source_top_iou=qa['source_projection']['min_iou'], source_uncertainty_mm=layout['source_uncertainty_mm'],
                               max_geometry_error_mm=max(abs(value) for row in qa['parts'] for value in row['errors_mm'] + row['center_error_mm']),
                               source_warnings=layout['source_warnings'], front_side_comparison='NOT_PROVIDED',
                               calibration=calibration, blend_reopen=qa['blend_reopen'], glb_reimport=qa['glb_reimport'])
            except SceneError as exc:
                summary.update(status='BLOCKED_NEEDS_CONFIRMATION', reason=str(exc))
                if (job / 'build').exists():
                    raise RuntimeError('Post-build QA failed; do not call blocked source a success') from exc
            state['results'].append(summary)
            (out / 'trial.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
            notice('Actual assembly worker result - ' + case['id'], json.dumps(summary, ensure_ascii=False))
        state['status'] = 'EXPERIMENT_COMPLETED_NOT_FINAL_APPROVAL'
    except Exception as exc:
        state.update(status='FAILED', error=str(exc))
        (out / 'failure.log').write_text(traceback.format_exc())
        notice('Actual assembly pipeline failure', traceback.format_exc()[-8000:], error=True)
        raise
    finally:
        (out / 'trial.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
        report = ('# Qwen + OCR → Blender: bản vẽ công khai độc lập\n\n'
                  'Ba thiết kế khác nhau, không phải crop của cùng bản vẽ. Ảnh/crop chọn có giám sát; '
                  'không cung cấp đáp án kích thước/contour JSON cho AI. Giữ 18 trách nhiệm chuyên gia.\n\n'
                  'BLEND/GLB nếu có chỉ chứa tấm rời theo sơ đồ cắt đã có tỷ lệ; chưa phải sản phẩm lắp ráp. '
                  'Tên cấu kiện, vị trí lắp, hình chiếu đứng/cạnh, bán kính dao và lỗ chốt thiếu dữ liệu: CẦN XÁC NHẬN. '
                  'Sai số dựng theo JSON khác độ chính xác nguồn ảnh; IoU chỉ đối chiếu hình chiếu tấm cắt. '
                  'Không render, không nghiệm thu tự động, không website, không dữ liệu khách hàng hoặc API trả phí.\n\n'
                  '```json\n' + json.dumps(state, ensure_ascii=False, indent=2) + '\n```\n')
        (out / 'REPORT_VI.md').write_text(report)
        manifest = {str(p.relative_to(out)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in out.rglob('*') if p.is_file()}
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
                summary.write(report)


if __name__ == '__main__':
    main()
