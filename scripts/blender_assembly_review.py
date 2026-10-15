"""Apply only checked placements and inspect actual solid intersections. No render."""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path
import sys
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hgcloud.assembly_constraints import assembly_gate


def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    value = abs(bm.calc_volume(signed=True)) * 1e9
    bm.free()
    return value


def vertices(ob):
    return [ob.matrix_world @ v.co for v in ob.data.vertices]


def bounds(ob):
    points = vertices(ob)
    return [[op(p[i] for p in points) * 1000 for i in range(3)] for op in [min, max]]


def inspect_pair(a, b):
    aa, bb = bounds(a), bounds(b)
    separations = [max(aa[0][i] - bb[1][i], bb[0][i] - aa[1][i], 0) for i in range(3)]
    lower = sum(v * v for v in separations) ** .5
    intersection = 0
    if not any(separations):
        copy = a.copy()
        copy.data = a.data.copy()
        bpy.context.collection.objects.link(copy)
        mesh = copy.data
        try:
            bpy.context.view_layer.objects.active = copy
            modifier = copy.modifiers.new('QA_intersection_only', 'BOOLEAN')
            modifier.operation = 'INTERSECT'
            modifier.solver = 'EXACT'
            modifier.object = b
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            intersection = volume(copy)
        finally:
            bpy.data.objects.remove(copy, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    # Vertex-to-triangle nearest distance is an UPPER bound; edge-edge minima
    # may be smaller. Never report this as an exact clearance measurement.
    distances = []
    for source, target in [(a, b), (b, a)]:
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bm.transform(target.matrix_world)
        tree = BVHTree.FromBMesh(bm)
        for point in vertices(source):
            hit = tree.find_nearest(point)
            if hit[0] is not None:
                distances.append(hit[3] * 1000)
        bm.free()
    upper = min(distances) if distances else None
    collided = intersection > .01
    return dict(parts=[a.name, b.name], intersection_volume_mm3=intersection,
                collision=collided, gap_lower_mm=lower,
                gap_upper_mm=0 if collided else upper,
                clearance_status='CẦN XÁC NHẬN: no verified design clearance',
                method='exact Boolean solid volume; AABB lower / vertex-surface upper distance bounds')


def main():
    source_blend, spec_path, plan_path, out = map(Path, sys.argv[sys.argv.index('--') + 1:])
    spec, plan = [json.loads(p.read_text()) for p in [spec_path, plan_path]]
    if hashlib.sha256(Path(spec['source']).read_bytes()).hexdigest() != spec['source_sha256']:
        raise ValueError('Source image changed')
    gate = assembly_gate(spec, plan)
    out.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.open_mainfile(filepath=str(source_blend.resolve()))
    objects = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
    if set(objects) != {p['id'] for p in spec['parts']}:
        raise ValueError('Saved BLEND part inventory differs from evidence')
    # Markers are annotations, never physical hardware. They are not moved
    # by the future assembly solver without a reviewed association.
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH':
            bpy.data.objects.remove(ob, do_unlink=True)
    for ident, placement in gate['approved_placements'].items():
        matrix = Matrix(placement['rotation']).to_4x4()
        matrix.translation = Vector(placement['translation_mm']) / 1000
        objects[ident].matrix_world = matrix
    for ob in objects.values():
        ob['placement_status'] = 'REVIEWED_ANNOTATION_CANDIDATE' if ob.name in gate['approved_placements'] else 'UNPLACED_SOURCE_CUT_LAYOUT'
        ob['review'] = 'CẦN XÁC NHẬN'
    bpy.context.view_layer.update()
    rows = []
    for part in spec['parts']:
        ob = objects[part['id']]
        actual = [(max(v.co[i] for v in ob.data.vertices) - min(v.co[i] for v in ob.data.vertices)) * 1000 for i in range(3)]
        expected = [max(p[i] for p in part['outline_mm']) - min(p[i] for p in part['outline_mm']) for i in range(2)] + [part['thickness_mm']]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bad_edges = sum(not edge.is_manifold for edge in bm.edges)
        bm.free()
        errors = [a - b for a, b in zip(actual, expected)]
        placement = gate['approved_placements'].get(ob.name)
        target_center = placement['translation_mm'] if placement else part['center_mm']
        target_rotation = placement['rotation'] if placement else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        position_errors = [ob.matrix_world.translation[i] * 1000 - target_center[i] for i in range(3)]
        rotation_error = max(abs(ob.matrix_world[i][j] - target_rotation[i][j]) for i in range(3) for j in range(3))
        if bad_edges or max(abs(v) for v in errors + position_errors) > .1 or rotation_error > 1e-6:
            raise ValueError('Part geometry/thickness differs from evidence: ' + ob.name)
        rows.append(dict(id=ob.name, actual_local_mm=actual, expected_local_mm=expected,
                         dimension_errors_mm=errors, world_bbox_mm=bounds(ob),
                         position_errors_mm=position_errors, orientation_error=rotation_error,
                         world_matrix=[list(row) for row in ob.matrix_world], nonmanifold_edges=bad_edges,
                         placement_status=ob['placement_status']))
    # Never compare unplaced panels at cut-layout coordinates to assembled panels.
    groups = [[objects[p] for p in gate['approved_placements']],
              [objects[p] for p in gate['blocked_parts']]]
    pairs = []
    for index, group in enumerate(groups):
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                pair = inspect_pair(a, b)
                pair['scope'] = 'assembled_candidates' if index == 0 else 'unplaced_cut_layout_ONLY'
                pairs.append(pair)
    status = 'FAIL' if any(p['collision'] for p in pairs) else 'PASS_MESH_CHECKS_ONLY'
    scope = 'assembly_candidate' if gate['complete_placement_evidence'] else 'parts_review_NOT_complete_assembly'
    basename = 'assembly_candidate' if gate['complete_placement_evidence'] else 'source_parts_review'
    blend, glb = out / (basename + '.blend'), out / (basename + '.glb')
    bpy.context.scene['test30_status'] = gate['status']
    bpy.context.scene['scope'] = scope
    reference_points = {name: [tuple(p) for p in vertices(ob)] for name, ob in objects.items()}
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    bpy.ops.export_scene.gltf(filepath=str(glb.resolve()), export_format='GLB', export_extras=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
    for row in rows:
        actual_matrix = bpy.data.objects[row['id']].matrix_world
        if max(abs(actual_matrix[i][j] - row['world_matrix'][i][j]) for i in range(4) for j in range(4)) > 1e-6:
            raise ValueError('BLEND reopen changed orientation')
        if max(abs(a - b) for av, bv in zip(bounds(bpy.data.objects[row['id']]), row['world_bbox_mm']) for a, b in zip(av, bv)) > .1:
            raise ValueError('BLEND reopen changed placement')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    imported = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
    if set(imported) != set(objects):
        raise ValueError('GLB part inventory changed')
    for row in rows:
        error = max(abs(a - b) for av, bv in zip(bounds(imported[row['id']]), row['world_bbox_mm']) for a, b in zip(av, bv))
        if error > .1:
            raise ValueError('GLB placement changed')
        row['glb_bbox_error_mm'] = error
        actual_points = [tuple(p) for p in vertices(imported[row['id']])]
        reference = reference_points[row['id']]
        vertex_error = 0
        for source_points, target_points in [(reference, actual_points), (actual_points, reference)]:
            tree = KDTree(len(target_points))
            for i, point in enumerate(target_points):
                tree.insert(point, i)
            tree.balance()
            vertex_error = max(vertex_error, max(tree.find(point)[2] * 1000 for point in source_points))
        if vertex_error > .1:
            raise ValueError('GLB world geometry changed despite matching bounding boxes')
        row['glb_bidirectional_vertex_error_mm'] = vertex_error
    report = dict(test='TEST 30', status=gate['status'], technical_status=status, scope=scope,
                  gate=gate, parts=rows, pair_checks=pairs, physical_hardware_added=0,
                  final_approved=False, next_test_allowed=False, render_executed=False,
                  collision_volume_noise_threshold_mm3=.01,
                  source_blend_sha256=hashlib.sha256(source_blend.read_bytes()).hexdigest(),
                  blend_reopen='PASS', glb_reimport='PASS')
    (out / 'assembly_qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(dict(status=gate['status'], technical_status=status, placed=len(gate['approved_placements']),
                          unplaced=len(gate['blocked_parts']), pairs=len(pairs)), ensure_ascii=False))


if __name__ == '__main__':
    main()
