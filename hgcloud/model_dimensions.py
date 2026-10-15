"""Parse explicit dimension phrases in real model text; no design-specific answers."""
import math
import re
from .core import SceneError

NUMBER = r'(\d+(?:\.\d+)?)'
UNIT = r'(mm|cm|m|inches|inch|in|["”″])'
PATTERN = re.compile(r'(?<![\w.,+−-])' + NUMBER + r'\s*' + UNIT + r'\s*tall\s*[x×]\s*' + NUMBER + r'\s*' + UNIT + r'\s*square\b', re.I)
SCALE = {'mm': 1, 'cm': 10, 'm': 1000, 'in': 25.4, 'inch': 25.4, 'inches': 25.4,
         '"': 25.4, '”': 25.4, '″': 25.4}


def candidates_from_model_text(text, source_sha256):
    """Only an explicit height × square phrase supports depth; no scale guessing."""
    if not isinstance(text, str) or len(text) > 100_000 or not re.fullmatch(r'[a-f0-9]{64}', source_sha256):
        raise SceneError('Invalid model text or source binding')
    readings = []
    for match in PATTERN.finditer(text):
        height, height_unit, width, width_unit = match.groups()
        height, width = float(height) * SCALE[height_unit.lower()], float(width) * SCALE[width_unit.lower()]
        if not all(math.isfinite(value) and 0 < value <= 100_000 for value in [height, width]):
            raise SceneError('Implausible dimension in model text')
        readings.append((height, width, match.group(0)))
    if not readings:
        raise SceneError('No supported explicit dimension phrase in actual model text')
    if any(abs(height - readings[0][0]) > .001 or abs(width - readings[0][1]) > .001 for height, width, quote in readings):
        raise SceneError('Conflicting model dimension readings; no cherry-picking against reference')
    height, width, quote = readings[0]
    return dict(status='MODEL_READ_DIMENSION_CANDIDATES', source_sha256=source_sha256,
                recognition_basis='Actual local model output text, parsed deterministically; not OCR reference',
                quoted_model_text=quote, units='mm',
                dimensions={axis: dict(value_mm=value, confidence='needs_confirmation',
                                       basis='explicit_square_relation_in_model_text' if axis == 'y' else 'printed_label_read_by_model',
                                       source_note=quote, bbox_px=None)
                            for axis, value in [('x', width), ('y', width), ('z', height)]},
                object_assignment='CẦN XÁC NHẬN', center_mm=None, scene_ready=False, build_allowed=False,
                unknown_details=['Exact text region', 'Assignment to the correct object/view', 'Shape and hidden construction'])


def compare_candidates(candidates, reference, tolerance_mm=1):
    if not candidates:
        return dict(status='NOT_COMPARABLE', reason='No model-read dimension candidates')
    errors = {axis: candidates['dimensions'][axis]['value_mm'] - value for axis, value in reference.items()}
    return dict(status='NUMERICAL_MATCH_ONLY_REVIEW_REQUIRED' if all(abs(value) <= tolerance_mm for value in errors.values()) else 'NUMERICAL_MISMATCH',
                errors_mm=errors, reference_mm=reference, tolerance_mm=tolerance_mm, build_allowed=False,
                limitation='Agreement with independent OCR is not object association, source localization or 3D shape verification')
