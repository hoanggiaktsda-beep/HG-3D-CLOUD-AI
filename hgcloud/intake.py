"""Local image intake and evidence-based observations; no external API calls."""
import csv
import hashlib
import io
import json
import math
import re
import subprocess
from pathlib import Path
from .core import SceneError, validate, ID_RE, STATES

INPUT_TYPES = {'technical_drawing', 'layout', 'product_photo', 'interior_photo'}


def receive(image, input_type, output):
    from PIL import Image
    if input_type not in INPUT_TYPES:
        raise SceneError('Unsupported input_type')
    image, output = Path(image), Path(output)
    data = image.read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise SceneError('Image exceeds 20 MiB')
    with Image.open(image) as im:
        im.verify()
    with Image.open(image) as im:
        if im.width * im.height > 25_000_000:
            raise SceneError('Image exceeds 25 megapixels')
        dimensions = [im.width, im.height]
    output.mkdir(parents=True, exist_ok=False)
    copied = output / ('source' + image.suffix.lower())
    copied.write_bytes(data)
    manifest = {'input_type': input_type, 'source': copied.name,
                'sha256': hashlib.sha256(data).hexdigest(), 'pixels': dimensions,
                'automatic_geometry_recognition': False,
                'observations': [], 'missing_information': [], 'ocr': []}
    if input_type in {'technical_drawing', 'layout'}:
        result = subprocess.run(['tesseract', str(copied), 'stdout', '--psm', '6', 'tsv'],
                                capture_output=True, text=True, timeout=60, check=True)
        lines = {}
        for row in csv.DictReader(io.StringIO(result.stdout), delimiter='\t'):
            if row['text'].strip() and float(row['conf']) >= 0:
                key = tuple(row[k] for k in ('page_num', 'block_num', 'par_num', 'line_num'))
                lines.setdefault(key, []).append(row)
        for rows in lines.values():
            text = ' '.join(r['text'] for r in rows)
            record = {'text': text, 'confidence': min(float(r['conf']) for r in rows),
                      'bbox_px': [min(int(r['left']) for r in rows), min(int(r['top']) for r in rows),
                                  max(int(r['left'])+int(r['width']) for r in rows),
                                  max(int(r['top'])+int(r['height']) for r in rows)]}
            # Deliberately narrow: unambiguous labelled dimensions, explicit units.
            match = re.fullmatch(r'(WIDTH|DEPTH|HEIGHT)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)', text, re.I)
            if match:
                record['dimension_candidate'] = {'axis': {'width': 'x', 'depth': 'y', 'height': 'z'}[match[1].lower()],
                                                  'value_mm': float(match[2])*{'mm': 1, 'cm': 10, 'm': 1000}[match[3].lower()],
                                                  'confidence': 'needs_confirmation'}
            manifest['ocr'].append(record)
    manifest['missing_information'] = ['Assign dimensions to objects and verify OCR against image',
                                       'Unseen structure is unknown; do not invent it']
    (output / 'intake.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def compile_scene(intake_path, observations_path):
    intake_path = Path(intake_path)
    intake = json.loads(intake_path.read_text())
    image = intake_path.parent / intake['source']
    if hashlib.sha256(image.read_bytes()).hexdigest() != intake['sha256']:
        raise SceneError('Source image changed since intake')
    observations = json.loads(Path(observations_path).read_text())
    provenance = observations.get('vision_provenance')
    if provenance and provenance.get('source_sha256') != intake['sha256']:
        raise SceneError('Vision response belongs to a different image')
    objects, pending = [], []
    for obs in observations['objects']:
        ident = obs.get('id', '')
        if not ID_RE.fullmatch(ident):
            raise SceneError('Invalid object id')
        size, evidence = [], {}
        for axis in 'xyz':
            item = obs.get('dimensions', {}).get(axis)
            if not item or item.get('value_mm') is None:
                pending.append(f'{ident}.{axis}: missing dimension')
                continue
            value = item['value_mm']
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise SceneError(f'{ident}.{axis}: invalid size')
            state = item.get('confidence')
            if state not in STATES or not isinstance(item.get('source_note'), str) or not item['source_note'].strip():
                raise SceneError('Dimension requires confidence and evidence')
            if state == 'confirmed':
                if item.get('basis') == 'drawing':
                    region = item.get('bbox_px')
                    if not (item.get('verified_by') and isinstance(region, list) and len(region) == 4
                            and all(type(v) in (int, float) and math.isfinite(v) for v in region)
                            and 0 <= region[0] < region[2] <= intake['pixels'][0]
                            and 0 <= region[1] < region[3] <= intake['pixels'][1]):
                        raise SceneError('Confirmed drawing dimension needs reviewed image region')
                elif item.get('basis') != 'user_measurement':
                    raise SceneError('OCR/pixels alone cannot confirm a dimension')
            if state == 'needs_confirmation':
                pending.append(f'{ident}.{axis}: unresolved dimension')
            size.append(value)
            evidence[axis] = item
        if len(size) != 3:
            continue
        # Layout has no implicit height; observations must explicitly supply all axes.
        center = obs.get('center_mm')
        placement = obs.get('placement_evidence')
        if not isinstance(placement, dict) or placement.get('confidence') not in STATES or not placement.get('source_note'):
            raise SceneError('Placement requires separate evidence')
        if placement['confidence'] == 'needs_confirmation':
            pending.append(f'{ident}: unresolved placement')
        states = [v['confidence'] for v in evidence.values()] + [placement['confidence']]
        overall = 'needs_confirmation' if 'needs_confirmation' in states else ('inferred' if 'inferred' in states else 'confirmed')
        unknown = obs.get('unknown_details', [])
        if not isinstance(unknown, list) or not all(isinstance(v, str) for v in unknown):
            raise SceneError('unknown_details must be strings')
        # No generative furniture internals: observed envelope only until parts are supplied.
        objects.append({'id': ident, 'kind': 'box', 'center_mm': center, 'size_mm': size,
                        'confidence': overall, 'source_note': 'Image evidence: ' + intake['sha256'],
                        'dimension_evidence': evidence, 'placement_evidence': placement,
                        'observed_kind': obs.get('kind', 'unknown'), 'unknown_details': unknown,
                        'representation': 'observed_envelope', 'material': 'default',
                        'rotation_deg': obs.get('rotation_deg', [0, 0, 0]),
                        'dimensions_tolerance_mm': obs.get('dimensions_tolerance_mm', 1)})
    if pending:
        raise SceneError('Build blocked: ' + '; '.join(pending))
    scene = {'schema_version': '1.0', 'project': observations['project'], 'units': 'mm',
             'source_images': [str(image.resolve())], 'objects': objects,
             'vision_provenance': provenance,
             'intake_evidence': {'sha256': intake['sha256'], 'input_type': intake['input_type'],
                                 'recognition': 'reviewed observations; OCR candidates are unconfirmed'}}
    return validate(scene)
