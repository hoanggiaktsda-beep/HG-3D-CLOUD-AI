"""Two public drawing crops, real larger CPU VLM; no customer file inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.intake import receive, compile_scene
from hgcloud.core import SceneError
from hgcloud.quantized_vision import QuantizedCPUVision
from hgcloud.model_dimensions import candidates_from_model_text, compare_candidates
from scripts.cloud_worker_sample import SOURCE_URL, verified_source
from scripts.public_vision_trial import download, notice, drawing_reference, compare_dimensions

MODEL_ID = 'Qwen/Qwen2-VL-2B-Instruct'
MODEL_REVISION = '895c3a49bc3fa70a340399125c650a463535e71c'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-cache', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status='STARTED', live_model_executed=False, results=[], build_allowed=False)
    try:
        from PIL import Image
        from huggingface_hub import HfApi, snapshot_download
        pdf = out / 'public-atfab.pdf'
        pdf.write_bytes(verified_source(download(SOURCE_URL)))
        for page in [3, 6]:
            subprocess.run(['pdftoppm', '-scale-to', '1800', '-f', str(page), '-l', str(page), '-singlefile', '-png', str(pdf), str(out / f'atfab-{page}')], check=True, timeout=60)
        with Image.open(out / 'atfab-3.png') as image:
            image.crop((25, 360, 610, 740)).save(out / 'printed-dimensions.png')
        info = HfApi().model_info(MODEL_ID, revision=MODEL_REVISION, files_metadata=True)
        license_name = (info.card_data.to_dict() if info.card_data else {}).get('license')
        if info.private or info.gated or license_name != 'apache-2.0':
            raise ValueError('Expected public ungated Apache-2.0 model')
        weights = [file for file in info.siblings if file.rfilename.endswith('.safetensors')]
        if not weights or any(file.size is None for file in weights) or sum(file.size for file in weights) > 6_000_000_000:
            raise ValueError('Larger CPU model exceeds six GB download limit')
        metadata = dict(model_id=MODEL_ID, revision=info.sha, license=license_name,
                        device='cpu', remote_code=False, weights_bytes=sum(file.size for file in weights))
        notice('Larger real CPU model provenance', json.dumps(metadata))
        snapshot = Path(snapshot_download(MODEL_ID, revision=info.sha, cache_dir=str(args.model_cache.resolve()),
                                         allow_patterns=['*.json', '*.safetensors', 'tokenizer.model', 'vocab.*', 'merges.txt']))
        metadata['safetensors_sha256'] = {str(p.relative_to(snapshot)): hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.rglob('*.safetensors')}
        provider = QuantizedCPUVision(snapshot, metadata)
        (out / 'model_provenance.json').write_text(json.dumps(metadata, indent=2))
        for name, source in [('full-drawing', out / 'atfab-3.png'), ('dimension-crop', out / 'printed-dimensions.png')]:
            job = out / name
            receive(source, 'technical_drawing', job)
            result = provider.analyze(job / 'intake.json')
            result['model_geometry_status'] = result['status']
            # Parse only actual model output BEFORE computing independent OCR reference.
            try:
                candidates = candidates_from_model_text(result['caption'] + '\n' + result['raw_geometry_response'], result['execution']['source_sha256'])
                (job / 'dimension_candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
                result['dimension_candidates'] = candidates
                result['status'] = 'DIMENSION_CANDIDATES_NEEDS_REVIEW'
            except SceneError as exc:
                candidates = None
                result['dimension_candidates'] = dict(status='UNSUPPORTED_OR_CONFLICTING_MODEL_TEXT', reason=str(exc), build_allowed=False)
            reference = drawing_reference(out / 'atfab-3.png', job)
            result['dimension_comparison'] = compare_dimensions(result['observations'], reference)
            result['model_text_dimension_comparison'] = compare_candidates(candidates, reference)
            if result['observations']:
                op = job / 'observations.json'
                op.write_text(json.dumps(result['observations'], ensure_ascii=False, indent=2))
                try:
                    compile_scene(job / 'intake.json', op)
                except SceneError as exc:
                    result['build_gate'] = str(exc)
                else:
                    raise RuntimeError('Unreviewed larger-model geometry bypassed gate')
            else:
                result['build_gate'] = 'BLOCKED: no valid grounded geometry'
            result['public_source'] = dict(url=SOURCE_URL, license='CC BY-NC-SA 3.0, PDF page 6',
                                         author='AtFAB / Filson and Rohrbacher 2013',
                                         supervised_crop=name == 'dimension-crop', reference_supplied_to_model=False)
            (job / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
            summary = {key: result[key] for key in ['status', 'caption', 'raw_geometry_response', 'dimension_comparison', 'build_gate', 'build_allowed']}
            summary.update(dimension_candidates=result['dimension_candidates'], model_text_dimension_comparison=result['model_text_dimension_comparison'])
            summary['model_geometry_status'] = result['model_geometry_status']
            summary.update(name=name, reason=result.get('reason'), inference_seconds=result['execution']['inference_seconds'])
            state['results'].append(summary)
            state['live_model_executed'] = True
            (out / 'experiment.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
            notice('Actual larger CPU vision result - ' + name, json.dumps(summary, ensure_ascii=False))
        state['status'] = 'EXPERIMENT_COMPLETED_NOT_ACCEPTED'
    except Exception as exc:
        state.update(status='FAILED', error=str(exc))
        (out / 'failure.log').write_text(traceback.format_exc())
        notice('Larger CPU experiment failed - not recognition success', traceback.format_exc()[-8000:], error=True)
        raise
    finally:
        (out / 'experiment.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
        report = ('# Thử mô hình lớn hơn bằng CPU, không render\n\n'
                  'Chỉ dùng bản vẽ AtFAB công khai, CC BY-NC-SA 3.0; không ảnh khách hàng. '
                  'Ảnh cắt được chọn có giám sát. Không đưa số đo tham chiếu vào model. '
                  'Không tự nghiệm thu, không API trả phí.\n\n```json\n' + json.dumps(state, ensure_ascii=False, indent=2) + '\n```\n')
        (out / 'REPORT_VI.md').write_text(report)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
                summary.write(report)


if __name__ == '__main__':
    main()
