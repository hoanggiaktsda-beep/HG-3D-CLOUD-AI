"""Real Blender worker for evidence-gated unassembled profiles. NEVER render."""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path
import sys
from mathutils import Vector

source, out = map(Path, sys.argv[sys.argv.index('--') + 1:])
spec = json.loads(source.read_text())
assert spec['schema'] == 'hg_cut_layout_v1' and not spec['assembly_allowed'] and spec['scope'] == 'unassembled_cut_layout_only'
assert hashlib.sha256(Path(spec['source']).read_bytes()).hexdigest() == spec['source_sha256']
out.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'


def plate(name, outline, thickness):
    n = len(outline)
    vertices = [(x / 1000, y / 1000, z / 1000) for z in [-thickness / 2, thickness / 2] for x, y in outline]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    return ob


for part in spec['parts']:
    ob = plate(part['id'], part['outline_mm'], part['thickness_mm'])
    ob.location = Vector(part['center_mm']) / 1000
    for hole in part['voids_mm']:
        cutter = plate('temporary_inside_cut', hole, part['thickness_mm'] * 3)
        cutter.location = ob.location
        bpy.context.view_layer.objects.active = ob
        modifier = ob.modifiers.new('observed_inside_cut', 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = cutter
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    ob['status'] = 'CẦN XÁC NHẬN'
    ob['scope'] = 'unassembled_cut_layout_only'
    ob['source_sha256'] = spec['source_sha256']
    ob['license'] = spec.get('license', 'See source evidence')
    ob['attribution'] = spec.get('attribution', 'See source evidence')
    ob['semantic_assignment'] = 'UNKNOWN'
    for i, (x, y) in enumerate(part['drill_markers_xy_mm']):
        marker = bpy.data.objects.new(part['id'] + '_drill_' + str(i), None)
        bpy.context.collection.objects.link(marker)
        marker.location = (x / 1000, y / 1000, part['thickness_mm'] / 1000 + .001)
        marker.empty_display_type = 'PLAIN_AXES'
        marker.empty_display_size = .005
        marker['diameter_mm'] = 'UNKNOWN'
        marker['status'] = 'CẦN XÁC NHẬN'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str((out / 'cut_layout.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out / 'cut_layout.glb').resolve()), export_format='GLB', export_extras=True)

# Reopen saved BLEND, then GLB, not just the in-memory construction data.
bpy.ops.wm.open_mainfile(filepath=str((out / 'cut_layout.blend').resolve()))
rows = []
for part in spec['parts']:
    ob = bpy.data.objects[part['id']]
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nonmanifold = sum(not edge.is_manifold for edge in bm.edges)
    volume = abs(bm.calc_volume(signed=True)) * 1e9
    degenerate = sum(face.calc_area() < 1e-14 for face in bm.faces)
    points = [[value * 1000 for value in ob.matrix_world @ vertex.co] for vertex in bm.verts]
    actual = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
    expected = [max(p[i] for p in part['outline_mm']) - min(p[i] for p in part['outline_mm']) for i in range(2)] + [part['thickness_mm']]
    errors = [a - b for a, b in zip(actual, expected)]
    centers = [(max(p[i] for p in points) + min(p[i] for p in points)) / 2 for i in range(3)]
    center_errors = [a - b for a, b in zip(centers, part['center_mm'])]
    assert not nonmanifold and not degenerate and volume > 0, (part['id'], nonmanifold, degenerate, volume)
    assert max(abs(value) for value in errors + center_errors) < .1, (part['id'], errors, center_errors)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    top_triangles = []
    for face in bm.faces:
        if face.normal.z > .9:
            top_triangles.append([[value * 1000 for value in ob.matrix_world @ vertex.co] for vertex in face.verts])
    rows.append(dict(id=part['id'], actual_mm=actual, expected_mm=expected, errors_mm=errors,
                     center_error_mm=center_errors, world_vertices_mm=points, top_triangles_mm=top_triangles,
                     nonmanifold_edges=nonmanifold, degenerate_faces=degenerate, volume_mm3=volume, passed=True))
    bm.free()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str((out / 'cut_layout.glb').resolve()))
bpy.context.view_layer.update()
imported = {ob.name: ob for ob in bpy.data.objects if ob.type == 'MESH'}
assert set(imported) == {part['id'] for part in spec['parts']}
for row in rows:
    ob = imported[row['id']]
    points = [ob.matrix_world @ vertex.co * 1000 for vertex in ob.data.vertices]
    errors = [abs(extreme(p[i] for p in points) - extreme(p[i] for p in row['world_vertices_mm']))
              for i in range(3) for extreme in [min, max]]
    assert max(errors) < .1, (row['id'], errors)
    row['glb_reimport_bbox_errors_mm'] = errors
markers = [ob for ob in bpy.data.objects if ob.type == 'EMPTY' and '_drill_' in ob.name]
expected_markers = sum(len(part['drill_markers_xy_mm']) for part in spec['parts'])
assert len(markers) == expected_markers and all(ob.get('diameter_mm') == 'UNKNOWN' for ob in markers)
report = dict(status='NEEDS_REVIEW', technical_status='PASS', scope=spec['scope'], parts=rows,
              render_executed=False, physical_drill_bores=0, drill_markers=expected_markers,
              assembly_verified=False, semantic_assignment='CẦN XÁC NHẬN',
              source_uncertainty_mm=spec['source_uncertainty_mm'], glb_reimport='PASS', blend_reopen='PASS',
              front_view_comparison='NOT_PROVIDED', side_view_comparison='NOT_PROVIDED')
(out / 'part_qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print('PASS real BLEND reopen, per-part dimensions/positions/topology and GLB reimport; NOT assembled product acceptance')
