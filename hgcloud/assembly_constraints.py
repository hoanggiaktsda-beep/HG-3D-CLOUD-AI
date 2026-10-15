"""Metric assembly from reviewed image annotations, never exploded-view guesses."""
import hashlib
from pathlib import Path
import re
import numpy as np
from .core import SceneError
from .vision import ROLES

VIEW_AXES = {'top': (0, 1), 'front': (0, 2), 'side': (1, 2)}


def instruction_relations(text):
    """Only explicit text relations; no numeric positions, angles or hardware sizes."""
    relations = []
    for match in re.finditer(r'slot\s+part\s+([A-Z])\s+into\s+part\s+([A-Z])', text, re.I):
        relations.append(dict(parts=[s.upper() for s in match.groups()], relation='slot_into',
                              source_quote=match.group(), metric_transform=None,
                              status='CẦN XÁC NHẬN'))
    for match in re.finditer(r'fit\s+side\s+parts\s+([A-Z])[,\s]+then\s+part\s+([A-Z])', text, re.I):
        relations.append(dict(parts=[s.upper() for s in match.groups()], relation='assembly_order',
                              source_quote=match.group(), metric_transform=None,
                              status='CẦN XÁC NHẬN'))
    for match in re.finditer(r'add\s+parts\s+([A-Z])\s*(?:&|and)\s*([A-Z])', text, re.I):
        relations.append(dict(parts=[s.upper() for s in match.groups()], relation='add_after_previous_steps',
                              source_quote=match.group(), metric_transform=None,
                              status='CẦN XÁC NHẬN'))
    return relations


def labelled_parts(text):
    """OCR bill-of-material observations, never an assignment to cut contours."""
    result = []
    for line in text.splitlines():
        match = re.fullmatch(r'\s*([A-Z])(?:\1)?\s+([A-Za-z ]+?)\s+(\d+)\s+(\d+)\s*', line, re.I)
        if match:
            label, name, count, _ = match.groups()
            result.append(dict(label=label.upper(), name=name.strip(), quantity=int(count),
                               source_quote=line, basis='OCR printed bill of materials',
                               contour_assignment=None, orientation=None, position_mm=None,
                               status='CẦN XÁC NHẬN'))
    return result


def rigid_transform(local, world, tolerance_mm):
    """Kabsch fit; three non-collinear anchors, no reflection or scale change."""
    a, b = np.asarray(local, dtype=float), np.asarray(world, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3 or len(a) < 3 or not np.isfinite([a, b]).all():
        raise SceneError('Missing/nonfinite 3D anchor correspondences')
    if not 0 < tolerance_mm <= 5:
        raise SceneError('Unreasonable anchor tolerance')
    ac, bc = a - a.mean(axis=0), b - b.mean(axis=0)
    if np.linalg.matrix_rank(ac, tol=1e-7) < 2 or np.linalg.matrix_rank(bc, tol=1e-7) < 2:
        raise SceneError('Collinear anchors do not determine orientation')
    u, _, vt = np.linalg.svd(ac.T @ bc)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1] *= -1
        rotation = vt.T @ u.T
    translation = b.mean(axis=0) - rotation @ a.mean(axis=0)
    errors = np.linalg.norm(a @ rotation.T + translation - b, axis=1)
    if max(errors) > tolerance_mm:
        raise SceneError('Anchors contradict a rigid assembly; scale/reflection/position mismatch')
    return rotation.tolist(), translation.tolist(), float(max(errors))


def verify_placement(part, proposal, source_sha256, document_sha256):
    """Trust boundary: annotations must be explicitly reviewed, not AI approval.

    This checks consistency/provenance of supplied annotations. It does NOT prove
    that a human reviewed them; callers must protect the review input channel.
    Public TEST 30 supplies no fabricated positive annotations.
    """
    if proposal.get('source_sha256') != source_sha256:
        raise SceneError('Assembly proposal belongs to another source image')
    if proposal.get('semantic_assignment_status') != 'confirmed':
        raise SceneError('Part-to-drawing label mapping needs confirmation')
    if proposal.get('anchor_review_status') != 'confirmed' or not proposal.get('anchor_source_note'):
        raise SceneError('Metric anchor mapping needs reviewed drawing evidence')
    tolerance = proposal.get('tolerance_mm', 0)
    rotation, center, residual = rigid_transform(proposal.get('local_anchors_mm', []),
                                               proposal.get('world_anchors_mm', []), tolerance)
    views = proposal.get('views', {})
    if set(views) != set(VIEW_AXES):
        raise SceneError('CẦN XÁC NHẬN: dimensioned top/front/side correspondence is missing')
    points = np.asarray([[x, y, z] for z in [-part['thickness_mm'] / 2, part['thickness_mm'] / 2]
                         for x, y in part['outline_mm']])
    transformed = points @ np.asarray(rotation).T + center
    comparisons = {}
    for view, axes in VIEW_AXES.items():
        evidence = views[view]
        if evidence.get('document_sha256') != document_sha256:
            raise SceneError('Mixed drawing documents in metric views: ' + view)
        if evidence.get('status') != 'confirmed' or evidence.get('basis') != 'reviewed_metric_annotation' or not evidence.get('source_note'):
            raise SceneError('Unreviewed metric image annotation: ' + view)
        image = Path(evidence['image_path'])
        if hashlib.sha256(image.read_bytes()).hexdigest() != evidence.get('image_sha256'):
            raise SceneError('View image changed: ' + view)
        expected = np.asarray(evidence.get('bbox_mm', []), dtype=float)
        if expected.shape != (4,) or not np.isfinite(expected).all() or np.any(expected[2:] <= expected[:2]):
            raise SceneError('Invalid view measurement: ' + view)
        actual = np.concatenate([transformed[:, axes].min(axis=0), transformed[:, axes].max(axis=0)])
        error = float(max(abs(actual - expected)))
        if error > tolerance:
            raise SceneError('Contradictory metric view: ' + view)
        comparisons[view] = dict(max_error_mm=error, source_note=evidence['source_note'])
    return dict(rotation=rotation, translation_mm=center, anchor_residual_mm=residual,
                views=comparisons, semantic_label=proposal['semantic_label'])


def assembly_gate(layout, plan):
    parts = layout['parts']
    proposals = plan.get('placements', {})
    if set(proposals) - {p['id'] for p in parts}:
        raise SceneError('Assembly refers to unknown source panels')
    approved, blocked = {}, {}
    for part in parts:
        try:
            if part['id'] not in proposals:
                raise SceneError('Missing label mapping, metric anchors and dimensioned top/front/side views')
            approved[part['id']] = verify_placement(part, proposals[part['id']], layout['source_sha256'],
                                                   layout.get('document_sha256', layout['source_sha256']))
        except (SceneError, KeyError, TypeError, ValueError, OSError) as exc:
            blocked[part['id']] = dict(status='CẦN XÁC NHẬN', reason=str(exc))
    complete = bool(parts) and not blocked
    requirements = dict(giữ_nguyên=['18 vai trò', 'hình học có chứng cứ', 'không render'],
                        được_thay_đổi=['bộ giải vị trí', 'kiểm định mesh và ảnh viewport'],
                        kích_thước_chắc_chắn='Chỉ nhãn/annotation đã đối chứng; không tự nâng raster lên confirmed',
                        kích_thước_chưa_chắc_chắn=['Tọa độ lắp', 'góc lắp', 'khe hở', 'đường kính khoan', 'chi tiết khuất'],
                        yêu_cầu_thêm_dữ_liệu='Hình chiếu có kích thước và ánh xạ mỗi contour sang nhãn cấu kiện')
    return dict(status='ASSEMBLY_CANDIDATE_NEEDS_REVIEW' if complete else 'BLOCKED_COMPLETE_ASSEMBLY',
                approved_placements=approved, blocked_parts=blocked, complete_placement_evidence=complete,
                final_approved=False, next_test_allowed=False, roles=ROLES, director_requirements=requirements,
                role_reviews=[dict(role=role, status='NEEDS_REVIEW',
                                   basis='Trách nhiệm kiểm tra; không tuyên bố 18 model/chuyên gia đã phê duyệt') for role in ROLES])
