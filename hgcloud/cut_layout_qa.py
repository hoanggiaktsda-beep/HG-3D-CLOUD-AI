"""Compare measured Blender top triangles with fresh segmentation of source PNG."""
from .core import SceneError
from .cut_layout import color_mask, closed_color_profiles


def verify_projection(spec, qa):
    import cv2
    import numpy as np
    if qa.get('render_executed') is not False or qa.get('assembly_verified') is not False:
        raise SceneError('Invalid acceptance scope')
    image = cv2.imread(spec['source'])
    x, y, width, height = spec['frame_px']
    crop = image[y:y + height, x:x + width]
    contours = closed_color_profiles(color_mask(crop, spec['calibration']['legend']['outside']))
    holes = closed_color_profiles(color_mask(crop, spec['calibration']['legend']['inside']))
    if len(contours) != len(qa['parts']):
        raise SceneError('Missing model parts')
    sx, sy = spec['mm_per_pixel']
    rows = []
    for contour, part, measured in zip(contours, spec['parts'], qa['parts']):
        if measured['id'] != part['id']:
            raise SceneError('Wrong part association')
        reference = np.zeros((height, width), np.uint8)
        polygon = np.asarray(contour, np.int32)
        cv2.fillPoly(reference, [polygon], 1)
        for hole in holes:
            if cv2.pointPolygonTest(polygon, tuple(np.asarray(hole).mean(axis=0)), False) > 0:
                cv2.fillPoly(reference, [np.asarray(hole, np.int32)], 0)
        actual = np.zeros_like(reference)
        for triangle in measured['top_triangles_mm']:
            pixels = np.rint([[point[0] / sx, height - 1 - point[1] / sy] for point in triangle]).astype('int32')
            cv2.fillPoly(actual, [pixels], 1)
        intersection = np.count_nonzero((actual != 0) & (reference != 0))
        union = np.count_nonzero((actual != 0) | (reference != 0))
        iou = intersection / union if union else 0
        if iou < .97:
            raise SceneError(f'Source top-view silhouette mismatch {part["id"]}: IoU {iou:.5f}')
        rows.append(dict(id=part['id'], source_top_iou=iou, passed=True,
                         source_precision_note='Calibrated raster, not original CAD tolerances'))
    return dict(status='PASS_SOURCE_TOP_PROJECTION_ONLY', parts=rows, min_iou=min(row['source_top_iou'] for row in rows),
                front='NOT_PROVIDED', side='NOT_PROVIDED', assembled_product='CẦN XÁC NHẬN')
