"""TEST 30: fixed public images, real OCR/Blender; never invent assembly poses."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import traceback
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.assembly_constraints import assembly_gate, instruction_relations, labelled_parts, require_complete_pages, metric_label
from hgcloud.assembly_evidence import parse_sheet, parse_thickness, parse_total, parse_legend
from hgcloud.cut_layout import extract_layout
from hgcloud.cut_layout_qa import verify_projection
from scripts.public_vision_trial import download, notice

SOURCES = [
    dict(id='atfab-chair', folder='OD-51381-5-To-30-Minute-Chair-1.0.0', code='OD-51381',
         sha256='e295e6496d2b5dc314175afc678bf7b0aa61d984dc52b7d53e50c4d602441445', pages=[1, 2, 3, 4, 5, 6, 7],
         author='AtFAB / Filson and Rohrbacher 2013', license='CC BY-NC-SA 3.0 (PDF page 7)'),
    dict(id='slim-chair-independent', folder='OD-55134-Slim-Chair-1.1.0', code='OD-55134',
         sha256='9930aaaac970f386fb516d48f0a190b069ef65c4fd36b091765d4d38800f54b0', pages=[1, 2],
         author='Jose Pacheco', license='CC BY 4.0 (source LICENSE); noncommercial test respecting PDF watermark'),
]


def command(args, log, timeout=180):
    result = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    log.write_text(result.stdout + result.stderr)
    result.check_returncode()
    return result.stdout


def ocr_crop(page, box, dest, rotate=0):
    with Image.open(page) as image:
        factor = image.height / 1800
        crop = image.crop(tuple(round(v * factor) for v in box))
        if rotate:
            crop = crop.rotate(rotate, expand=True)
        crop.save(dest)
    return command(['tesseract', dest, 'stdout', '--psm', '6'], dest.with_suffix('.txt'), 60)


def blender(script, args, log):
    command(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', ROOT / 'scripts' / script, '--', *args], log, 240)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--capture-viewport', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = dict(test='TEST 30', status='RUNNING', results=[], final_approved=False,
                 next_test_allowed=False, render_executed=False, paid_api_called=False,
                 new_qwen_inference_executed=False,
                 analysis_method='Real OCR/CV + Codex-assisted visual source review, not autonomous Qwen assembly',
                 previous_live_qwen_run='https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38694666996')
    try:
        for source in SOURCES:
            job = out / source['id']
            job.mkdir()
            base = 'https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/' + source['folder'] + '/'
            pdf = job / 'public-source.pdf'
            data = download(base + source['code'] + '-Assembly-Guide.pdf')
            if hashlib.sha256(data).hexdigest() != source['sha256']:
                raise ValueError('Public PDF changed; source review must be repeated')
            pdf.write_bytes(data)
            info = command(['pdfinfo', pdf], job / 'pdfinfo.txt', 30)
            count = int(re.search(r'^Pages:\s*(\d+)', info, re.M).group(1))
            require_complete_pages(count, source['pages'])
            (job / 'LICENSE-source.txt').write_bytes(download(base + 'LICENSE.txt'))
            provenance = dict(source, url=base + source['code'] + '-Assembly-Guide.pdf',
                              input='raster PNG only; no CAD/vector/geometry JSON input',
                              source_review='Codex assisted, fixed reviewed PDF hashes; not a new live Qwen run')
            (job / 'source.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
            pages = {}
            for page in source['pages']:
                prefix = job / ('page-' + str(page))
                command(['pdftoppm', '-scale-to', '4800', '-f', page, '-l', page, '-singlefile', '-png', pdf, prefix], job / ('raster-' + str(page) + '.log'), 60)
                pages[page] = prefix.with_suffix('.png')
            plan = dict(placements={}, view_inventory=dict(top=None, front=None, side=None),
                        reason='No reviewed metric 3D anchors and part-to-contour mapping; view availability is recorded separately',
                        physical_hardware_allowed=False)
            if source['id'] == 'atfab-chair':
                page_digest = hashlib.sha256(pages[3].read_bytes()).hexdigest()
                plan['view_inventory'] = {name: dict(page=3, image_sha256=page_digest, roi_at_1800=roi,
                                                    status='SOURCE_VIEW_PRESENT_NOT_YET_REGISTERED_PER_PART')
                                          for name, roi in [('top', [520, 545, 800, 790]),
                                                            ('front', [920, 900, 1140, 1260]),
                                                            ('side', [510, 890, 780, 1260])]}
                plan['dimension_ocr'] = {}
                for label, box, rotation in [('width_range', [475, 555, 515, 740], 270),
                                             ('overall_height', [840, 1020, 875, 1255], 270),
                                             ('seat_height', [795, 1040, 835, 1255], 270),
                                             ('depth', [585, 748, 685, 798], 0)]:
                    text = ocr_crop(pages[3], box, job / (label + '.png'), rotation)
                    plan['dimension_ocr'][label] = dict(metric_label(text), page=3, roi_at_1800=box,
                                                        rotation_degrees=rotation)
                cut_text = ocr_crop(pages[4], [30, 400, 520, 740], job / 'cut-context.png')
                material_text = ocr_crop(pages[6], [30, 600, 445, 1020], job / 'material.png')
                table_text = ocr_crop(pages[5], [30, 1110, 445, 1340], job / 'parts-table.png')
                assembly_text = ocr_crop(pages[5], [30, 480, 450, 630], job / 'assembly-instructions.png')
                plan['relations'] = instruction_relations(assembly_text)
                plan['part_label_observations'] = labelled_parts(table_text)
                plan['instruction_source_sha256'] = hashlib.sha256((job / 'assembly-instructions.png').read_bytes()).hexdigest()
                calibration = dict(sheet_mm=parse_sheet(cut_text), thickness_mm=parse_thickness(material_text),
                                   part_count=parse_total(table_text), legend=parse_legend(cut_text),
                                   scope='unassembled_cut_layout_only', confidence='inferred_calibrated_raster',
                                   basis='Actual OCR of fixed public image labels, Codex assisted visual review',
                                   status='CẦN XÁC NHẬN', assembly_allowed=False)
                layout = extract_layout(pages[4], calibration)
                layout.update(document_sha256=source['sha256'], license=source['license'], attribution=source['author'],
                              source_url=provenance['url'])
                spec_path = job / 'source-cut-layout.json'
                spec_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2))
                plan_path = job / 'assembly-plan.json'
                plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
                blender('blender_cut_layout.py', [spec_path, job / 'source-build'], job / 'source-blender.log')
                source_qa_path = job / 'source-build/part_qa.json'
                source_qa = json.loads(source_qa_path.read_text())
                source_qa['source_projection'] = verify_projection(layout, source_qa)
                source_qa_path.write_text(json.dumps(source_qa, ensure_ascii=False, indent=2))
                blender('blender_assembly_review.py', [job / 'source-build/cut_layout.blend', spec_path, plan_path, job / 'review-build'], job / 'review-blender.log')
                qa = json.loads((job / 'review-build/assembly_qa.json').read_text())
                if qa['technical_status'] != 'PASS_MESH_CHECKS_ONLY':
                    raise ValueError('Actual mesh QA failed; inspect Blender report')
                captures = []
                if args.capture_viewport:
                    if not os.environ.get('DISPLAY'):
                        raise ValueError('Real GUI DISPLAY required; never substitute rendered pictures')
                    command(['blender', '-t', '2', '--python', ROOT / 'scripts/capture_assembly_viewport.py', '--',
                             job / 'review-build/source_parts_review.blend', job / 'viewport'], job / 'viewport.log', 100)
                    captures = json.loads((job / 'viewport/capture_manifest.json').read_text())
                    if len(captures) != 4:
                        raise ValueError('Incomplete real viewport capture')
                result = dict(case=source['id'], status=qa['status'], technical_status=qa['technical_status'],
                              source=provenance, parts=len(qa['parts']), placed=0,
                              scoped_pair_checks=len(qa['pair_checks']), collisions=sum(p['collision'] for p in qa['pair_checks']),
                              pair_scope='unplaced cut layout, NOT assembled chair',
                              source_min_iou=source_qa['source_projection']['min_iou'],
                              source_uncertainty_mm=layout['source_uncertainty_mm'],
                              max_part_error_mm=max(abs(v) for p in qa['parts'] for v in p['dimension_errors_mm'] + p['position_errors_mm']),
                              relationships=plan['relations'], part_label_observations=plan['part_label_observations'],
                              view_inventory=plan['view_inventory'], orthographic_ocr=plan['dimension_ocr'],
                              captures=captures, render=False,
                              outputs=['review-build/source_parts_review.blend', 'review-build/source_parts_review.glb'],
                              blend_reopen=qa['blend_reopen'], glb_reimport=qa['glb_reimport'],
                              confirmed_assembly_exported=False)
            else:
                for page, image in pages.items():
                    command(['tesseract', image, 'stdout', '--psm', '6'], job / ('ocr-' + str(page) + '.txt'), 60)
                gate = assembly_gate(dict(parts=[], source_sha256=source['sha256']), plan)
                (job / 'assembly_gate.json').write_text(json.dumps(gate, ensure_ascii=False, indent=2))
                result = dict(case=source['id'], source=provenance, status=gate['status'], parts=0, placed=0,
                              confirmed_assembly_exported=False, outputs=[],
                              reason='Exploded drawing without verified part dimensions/thickness or orthographic metric views; no arbitrary geometry built')
            state['results'].append(result)
            notice('TEST 30 actual result ' + source['id'], json.dumps(result, ensure_ascii=False))
        state['status'] = 'BLOCKED_COMPLETE_ASSEMBLY_NEEDS_CONFIRMATION'
    except Exception:
        state['status'] = 'EXECUTION_FAILED'
        (out / 'failure.log').write_text(traceback.format_exc())
        notice('TEST 30 execution failure', traceback.format_exc(), error=True)
        raise
    finally:
        (out / 'test30.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
        report = ('# TEST 30 — kiểm định lắp ráp\n\n'
                  '**CHƯA ĐẠT mục tiêu lắp ráp hoàn chỉnh; chưa chuyển TEST 31.**\n\n'
                  'Giữ 18 trách nhiệm chuyên gia; không tuyên bố 18 model đã chạy/phê duyệt. '
                  'OCR/CV thật và kiểm tra nguồn có giám sát; không giả lập suy luận Qwen mới.\n\n'
                  'BLEND/GLB và viewport nếu có chỉ là bộ phận rời tại tọa độ sơ đồ cắt, '
                  'không phải mô hình ghế đã lắp. Kiểm va chạm/khe hở trong sơ đồ cắt không '
                  'chứng minh khả năng lắp ráp. Khoảng cách là cận dưới/cận trên, chưa có '
                  'khe hở thiết kế được xác nhận. Không tự thêm lỗ khoan hay liên kết.\n\n'
                  'AtFAB có mặt bằng/đứng/cạnh và kích thước ở trang 3; đã OCR nhãn d, h, H và '
                  'khoảng w. Khoảng w không được chọn tùy ý thành kích thước cố định. '
                  'CẦN XÁC NHẬN: ánh xạ contour sang A–F; điểm đối ứng 3D giữa các hình chiếu; '
                  'hướng/góc/vị trí lắp; khe lắp; đường kính và '
                  'chiều sâu khoan; bán kính dao và chi tiết khuất. Thứ tự B→D, C→E không '
                  'xác định được các thông số này. Không dùng gợi ý chế tạo chung làm kích '
                  'thước liên kết riêng của ghế.\n\n```json\n' + json.dumps(state, ensure_ascii=False, indent=2) + '\n```\n')
        (out / 'REPORT_TEST30_VI.md').write_text(report)
        manifest = {str(p.relative_to(out)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in out.rglob('*') if p.is_file()}
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as file:
                file.write(report)


if __name__ == '__main__':
    main()
