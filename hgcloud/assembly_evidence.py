"""Agree independent image readings; never promote an assembled product from cut data."""
import hashlib
import math
from pathlib import Path
import re
from .core import SceneError

COLORS = 'black|red|cyan|green|magenta|blue'


def unique(values, label):
    values = sorted(set(values))
    if len(values) != 1:
        raise SceneError('CẦN XÁC NHẬN: missing/conflicting ' + label)
    return values[0]


def parse_sheet(text):
    number = r'(\d+(?:\.\d+)?)'
    foot = r'(?:[\'’′]|ft\b|feet\b|foot\b)'
    pairs = re.findall(r'(?<![\w.,+−-])' + number + r'\s*' + foot + r'\s*[x×]\s*' + number + r'\s*' + foot, text, re.I)
    pairs = [tuple(sorted((float(a) * 304.8, float(b) * 304.8))) for a, b in pairs]
    dims = unique(pairs, 'explicit sheet dimensions in feet')
    if not 100 <= dims[0] <= dims[1] <= 10000:
        raise SceneError('Implausible sheet scale')
    return dims


def parse_thickness(text):
    values = [float(value) for value in re.findall(r'(?<![\w.,+−-])(\d+(?:\.\d+)?)\s*mm\b', text, re.I)]
    value = unique(values, 'explicit material mm label')
    if not 1 <= value <= 100:
        raise SceneError('Implausible sheet thickness')
    return value


def parse_total(text):
    # Formatting only: preserve words, digits, signs and units from live output.
    text = re.sub(r'[*|`]', ' ', text)
    value = unique([int(v) for v in re.findall(r'total\s+per\s+file\s*[:=]?\s*(\d+)\b', text, re.I)], 'total parts per file')
    if not 1 <= value <= 500:
        raise SceneError('Implausible part count')
    return value


def parse_legend(text):
    result = {}
    for name, words in [('outside', r'outside\s+cuts'), ('inside', r'inside\s+cuts'), ('drill', r'drill(?:ed)?\s+holes')]:
        values = re.findall(r'\b(' + COLORS + r')\s+(?:lines?|circles?)\s*[:=\s*]*' + words, text, re.I)
        result[name] = unique([v.lower() for v in values], name + ' color legend')
    if len(set(result.values())) != 3:
        raise SceneError('Ambiguous color roles')
    return result


def verified_reading(record, document_sha256):
    execution = record.get('execution', {})
    if not execution.get('live_model_executed') or execution.get('backend') != 'qwen2vl_cpu_live':
        raise SceneError('No actual Qwen inference evidence')
    if execution.get('model_revision') != '895c3a49bc3fa70a340399125c650a463535e71c':
        raise SceneError('Unverified model revision')
    if record.get('document_sha256') != document_sha256:
        raise SceneError('Mixed source documents')
    data = Path(record['image_path']).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != record.get('image_sha256') or digest != execution.get('image_sha256') or digest != record.get('ocr_image_sha256'):
        raise SceneError('AI/OCR source image mismatch')
    return record['ai_text'], record['ocr_text']


def agree_calibration(records, document_sha256):
    by_kind = {}
    for record in records:
        if record['purpose'] in by_kind:
            raise SceneError('Duplicate evidence purpose')
        by_kind[record['purpose']] = verified_reading(record, document_sha256)
    for name in ['cut_context', 'material', 'parts_table']:
        if name not in by_kind:
            raise SceneError('CẦN XÁC NHẬN: missing ' + name + ' evidence')
    if not all(re.search(r'digital\s+cut\s+file', text, re.I) and re.search(r'\bsheet\b', text, re.I) for text in by_kind['cut_context']):
        raise SceneError('View is not independently identified as a sheet cut layout')
    result = {}
    for field, purpose, parser in [('sheet_mm', 'cut_context', parse_sheet), ('thickness_mm', 'material', parse_thickness),
                                    ('part_count', 'parts_table', parse_total), ('legend', 'cut_context', parse_legend)]:
        a, b = [parser(text) for text in by_kind[purpose]]
        if a != b:
            raise SceneError('CẦN XÁC NHẬN: AI/OCR disagree on ' + field)
        result[field] = a
    hole_counts = [re.findall(r'total\s+per\s+file\s+\d+\s+\d+\s*\+\s*(\d+)\s+holes', re.sub(r'[*|`]', ' ', text), re.I) for text in by_kind['parts_table']]
    if all(len(values) == 1 for values in hole_counts) and hole_counts[0] == hole_counts[1]:
        result['printed_hole_count'] = int(hole_counts[0][0])
    result.update(scope='unassembled_cut_layout_only', confidence='inferred_calibrated_raster',
                  status='CẦN XÁC NHẬN', assembly_allowed=False,
                  thickness_note='Explicit nominal mm label; rounded inch equivalent is not actual material measurement')
    return result


def view_and_part_candidates(ai_text, ocr_text):
    """Text-only observations, not spatial assignment or validated view correspondence."""
    terms = ['seat back', 'seat', 'front legs', 'back legs', 'sides', 'feet', 'leg', 'beam', 'top', 'peg', 'lock']
    labels = [term for term in terms if re.search(r'\b' + term + r'\b', ai_text, re.I) and re.search(r'\b' + term + r'\b', ocr_text, re.I)]
    cut = all(re.search(r'digital\s+cut\s+file', text, re.I) for text in [ai_text, ocr_text])
    return dict(view_candidate='cut_layout' if cut else 'CẦN XÁC NHẬN',
                part_label_candidates=labels, semantic_assignment='CẦN XÁC NHẬN',
                front_side_top_correspondence='CẦN XÁC NHẬN', assembled_positions_mm=None)
