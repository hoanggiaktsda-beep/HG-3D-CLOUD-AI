"""Actual raster contours + explicit sheet calibration; no CAD vectors or guessed scale."""
import hashlib
from pathlib import Path
from .core import SceneError


def color_mask(image, color):
    import cv2
    import numpy as np
    r, g, b = [image[:, :, i].astype('int16') for i in [2, 1, 0]]
    masks = {'black': (r < 110) & (g < 110) & (b < 110),
             'red': (r > 150) & (g < 150) & (b < 150),
             'cyan': (r < 150) & (g > 150) & (b > 150),
             'green': (g > 100) & (g > r * 1.4) & (g > b * 1.4),
             'magenta': (r > 150) & (b > 150) & (g < 150),
             'blue': (b > 150) & (r < 150) & (g < 150)}
    if color not in masks:
        raise SceneError('Unsupported cut color')
    return masks[color].astype(np.uint8) * 255


def sheet_frame(image, sheet_mm):
    import cv2
    height, width = image.shape[:2]
    black = color_mask(image, 'black')
    contours, _ = cv2.findContours(black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if y < height * .2 or w * h < width * height * .12:
            continue
        # A closed, axis-aligned rectangular boundary, not an artwork's bbox.
        polygon = cv2.approxPolyDP(contour, .002 * cv2.arcLength(contour, True), True)
        if len(polygon) != 4 or abs(cv2.contourArea(contour) / ((w - 1) * (h - 1)) - 1) > .01:
            continue
        short, long = sorted(sheet_mm)
        dims = (short, long) if w < h else (long, short)
        sx, sy = dims[0] / (w - 1), dims[1] / (h - 1)
        if abs(sx / sy - 1) > .02:
            continue
        candidates.append((x, y, w, h, sx, sy))
    if len(candidates) != 1:
        raise SceneError('CẦN XÁC NHẬN: no unique undistorted sheet frame with explicit scale')
    return candidates[0]


def closed_color_profiles(mask):
    import cv2
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return []
    result = []
    for i, contour in enumerate(contours):
        parent, child = hierarchy[0][i][3], hierarchy[0][i][2]
        if parent != -1 or child == -1 or abs(cv2.contourArea(contours[child])) < 20:
            continue
        if hierarchy[0][child][0] != -1:
            raise SceneError('Multiple inner regions in a cut stroke; ambiguous contour')
        result.append(contour[:, 0, :].tolist())
    return sorted(result, key=lambda p: (min(x[1] for x in p), min(x[0] for x in p)))


def extract_layout(image_path, calibration):
    import cv2
    import numpy as np
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        raise SceneError('Invalid raster image')
    x, y, w, h, sx, sy = sheet_frame(image, calibration['sheet_mm'])
    crop = image[y:y + h, x:x + w]
    outside = closed_color_profiles(color_mask(crop, calibration['legend']['outside']))
    inside = closed_color_profiles(color_mask(crop, calibration['legend']['inside']))
    if len(outside) != calibration['part_count']:
        raise SceneError(f'CẦN XÁC NHẬN: observed {len(outside)} closed parts vs independent table {calibration["part_count"]}')
    n, labels, stats, centers = cv2.connectedComponentsWithStats(color_mask(crop, calibration['legend']['drill']))
    markers = [center.tolist() for i, center in enumerate(centers) if i and stats[i, cv2.CC_STAT_AREA] >= 2]
    parts = []
    def mm(point):
        return [point[0] * sx, (h - 1 - point[1]) * sy]
    for i, outline in enumerate(outside):
        polygon = np.asarray(outline, dtype=np.float32)
        holes = [hole for hole in inside if cv2.pointPolygonTest(polygon, tuple(np.asarray(hole).mean(axis=0)), False) > 0]
        points = [mm(point) for point in outline]
        center = [(min(p[j] for p in points) + max(p[j] for p in points)) / 2 for j in range(2)]
        local = lambda pts: [[v[0] - center[0], v[1] - center[1]] for v in [mm(p) for p in pts]]
        part_markers = [mm(p) for p in markers if cv2.pointPolygonTest(polygon, tuple(p), False) > 0]
        parts.append(dict(id=f'observed_panel_{i + 1:02}', outline_mm=local(outline), voids_mm=[local(hole) for hole in holes],
                          center_mm=[*center, calibration['thickness_mm'] / 2], thickness_mm=calibration['thickness_mm'],
                          source_outline_px=[[p[0] + x, p[1] + y] for p in outline],
                          drill_markers_xy_mm=part_markers, drill_diameter_mm=None,
                          semantic_assignment='CẦN XÁC NHẬN', assembly_position_mm=None,
                          confidence='inferred_calibrated_raster', status='CẦN XÁC NHẬN'))
    if sum(len(p['voids_mm']) for p in parts) != len(inside) or sum(len(p['drill_markers_xy_mm']) for p in parts) != len(markers):
        raise SceneError('Unassigned inside cuts or drill symbols')
    warnings = ['Semantic part names and assembled positions are unverified', 'Drill diameter and exact tool radii need confirmation']
    if calibration.get('printed_hole_count') is not None and len(markers) != calibration['printed_hole_count']:
        warnings.append(f'Observed drill symbols {len(markers)} differ from printed hole count {calibration["printed_hole_count"]}; no physical bores created')
    return dict(schema='hg_cut_layout_v1', source=str(image_path.resolve()),
                source_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest(), calibration=calibration,
                frame_px=[x, y, w, h], mm_per_pixel=[sx, sy], source_uncertainty_mm=max(sx, sy) * 2,
                origin='lower-left sheet border; XY cut layout; NOT assembled furniture coordinates',
                parts=parts, source_warnings=warnings, status='NEEDS_REVIEW', scope='unassembled_cut_layout_only', assembly_allowed=False)
