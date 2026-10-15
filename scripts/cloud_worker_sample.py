"""Public, supervised raster/OCR trial. No vision service, replay, or rendering."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from hgcloud.raster_profile import trace

SOURCE_URL = ('https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/'
              'OD-51384-Rotational-Stools-1.0.0/OD-51384-Assembly-Guide.pdf')
SOURCE_SHA256 = 'e7ab9a6da6e9d5639cbf99f9b69f5b522f5782ee1730be0836b765f2623fed65'


def verified_source(data):
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError('Public source checksum changed; review source, do not silently accept')
    return data


def dimensions_from_ocr(size_text, thickness_text):
    size = re.search(r'\((\d+(?:\.\d+)?)\W+\s*tall x (\d+(?:\.\d+)?)\W+\s*square', size_text)
    thick = re.search(r'(\d+(?:\.\d+)?)\s*\(', thickness_text)
    if not size or not thick:
        raise ValueError('Required printed dimensions not recognized; no fallback dimensions')
    height, width = [float(value) * 25.4 for value in size.groups()]
    thickness = float(thick[1])
    if not all(0 < value < 10000 for value in [height, width, thickness]) or thickness >= min(width, height):
        raise ValueError('Implausible OCR dimensions')
    return dict(width=width, depth=width, height=height, thickness=thickness)


def verify_qa(qa, dimensions):
    if len(qa['objects']) != 5 or not all(row['pass'] for row in qa['objects']):
        raise ValueError('Per-object Blender QA failed')
    if qa['drill_markers'] != 16 or qa['glb_drill_markers'] != 16 or qa['physical_drill_bores'] != 0:
        raise ValueError('Unknown bores must remain markers')
    vertices = [p for row in qa['objects'] for p in row['world_vertices_m']]
    measured = [(max(p[i] for p in vertices) - min(p[i] for p in vertices)) * 1000 for i in range(3)]
    errors = [abs(a - dimensions[k]) for a, k in zip(measured, ['width', 'depth', 'height'])]
    if max(errors) >= .1 or qa['render_executed'] is not False:
        raise ValueError('Envelope mismatch or render flag')
    return measured, errors


def run(command, log):
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(result.stdout)
    print(result.stdout, flush=True)
    result.check_returncode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    data = verified_source(urllib.request.urlopen(SOURCE_URL, timeout=60).read())
    pdf = out / 'public-source.pdf'
    pdf.write_bytes(data)
    # Only raster PNGs enter recognition. Never read PDF vectors, DXF, or design JSON.
    for page in [3, 4, 6]:
        run(['pdftoppm', '-scale-to', '1800', '-f', str(page), '-l', str(page), '-singlefile', '-png', str(pdf), str(out / f'page-{page}')], out / f'raster-{page}.log')
    texts = []
    for page, roi, name in [(3, (25, 360, 610, 740), 'size'), (4, (25, 360, 500, 540), 'thickness')]:
        with Image.open(out / f'page-{page}.png') as image:
            if image.size != (1391, 1800):
                raise ValueError('Source raster layout changed; supervised ROI review required')
            image.crop(roi).save(out / f'{name}-ocr.png')
        run(['tesseract', str(out / f'{name}-ocr.png'), 'stdout', '--psm', '6'], out / f'{name}-ocr.txt')
        texts.append((out / f'{name}-ocr.txt').read_text())
    dimensions = dimensions_from_ocr(*texts)
    source = out / 'page-4.png'
    evidence = dict(dimensions_mm=dimensions, source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    profiles={'side': trace(source, (620, 757, 726, 926)), 'seat': trace(source, (513, 819, 618, 925))},
                    status='CẦN XÁC NHẬN', recognition='Tesseract OCR + supervised fixed image ROIs, NOT autonomous vision AI',
                    dimension_confidence='confirmed printed nominal labels; source raster geometry inferred',
                    assembly_status='inferred from illustrated rotational assembly; exact fitting clearances unknown',
                    license='AtFAB / Filson and Rohrbacher 2013, CC BY-NC-SA 3.0 (PDF page 6)',
                    source_url=SOURCE_URL, source_pdf_sha256=SOURCE_SHA256)
    evidence_path = out / 'profile_evidence.json'
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(ROOT / 'scripts/blender_profile_build.py'), '--', str(evidence_path), str(out / 'model')], out / 'blender-build.log')
    run(['blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(ROOT / 'scripts/blender_worker_verify.py'), '--', str(out / 'model'), str(evidence_path)], out / 'blender-reopen.log')
    qa = json.loads((out / 'model/object_qa.json').read_text())
    measured, errors = verify_qa(qa, dimensions)
    glb = (out / 'model/detailed_draft.glb').read_bytes()
    if struct.unpack('<4sII', glb[:12]) != (b'glTF', 2, len(glb)):
        raise ValueError('Invalid GLB header or truncated file')
    report = ('# HG 3D CLOUD WORKER — kiểm thử mẫu công khai\n\n'
              'Kết quả kỹ thuật: PASS. Trạng thái thiết kế: **CẦN XÁC NHẬN**, không tự nghiệm thu.\n\n'
              f'Nguồn: {SOURCE_URL}\n\n'
              'AtFAB / Filson and Rohrbacher, 2013. CC BY-NC-SA 3.0 theo trang 6 PDF; '
              'bản dựng sửa đổi dùng cùng giấy phép, ghi công, phi thương mại.\n\n'
              f'Kích thước danh nghĩa đọc OCR (mm): {dimensions}.\n\n'
              f'Kích thước hình học Blender thực (mm): {measured}; sai lệch: {errors}.\n\n'
              'Đã kiểm tra 5 mesh riêng, độ dày, vị trí, manifold, thể tích, lỗ giữa mặt ghế; '
              'mở lại BLEND và nhập lại GLB, đối chiếu bbox từng đối tượng < 0,1 mm. '
              'Đây là sai số dựng theo số đọc, không phải độ chính xác biên dạng bản gốc.\n\n'
              'AI thị giác: **CHƯA KẾT NỐI**. OCR thật và vùng ảnh đã chọn có giám sát; '
              'không dùng AI giả hay dữ liệu hình học có sẵn. Biên dạng từ pixel, bố trí lắp ráp suy luận. '
              '16 ký hiệu khoan giữ dạng marker, không tạo lỗ chưa biết đường kính. '
              'Bán kính dao, thoát dao chính xác, dung sai và liên kết khuất: CẦN XÁC NHẬN. '
              'Chưa kiểm chứng tự nhận diện ảnh bất kỳ hoặc độ giống bằng AI.\n\n'
              'Không render. Không gửi dữ liệu khách hàng. Đây là worker batch mẫu, chưa nối API riêng tư.\n')
    (out / 'REPORT_VI.md').write_text(report)
    files = {str(p.relative_to(out)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'manifest.json').write_text(json.dumps(dict(status='PASS_TECHNICAL_NEEDS_REVIEW', files=files), indent=2))
    print(report)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(report + '\nArtifact manifest:\n```json\n' + json.dumps(files, indent=2) + '\n```\n')


if __name__ == '__main__':
    main()
