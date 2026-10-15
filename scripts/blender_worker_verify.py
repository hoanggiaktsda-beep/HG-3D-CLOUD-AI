"""Independently reopen the saved BLEND and measure actual mesh coordinates."""
import json
from pathlib import Path
import sys
import bpy

folder, evidence_path = map(Path, sys.argv[sys.argv.index('--') + 1:])
evidence = json.loads(evidence_path.read_text())
qa = json.loads((folder / 'object_qa.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder / 'detailed_draft.blend'))
bpy.context.view_layer.update()
meshes = {ob.name: ob for ob in bpy.data.objects if ob.type == 'MESH'}
assert set(meshes) == {row['id'] for row in qa['objects']}
for row in qa['objects']:
    points = [meshes[row['id']].matrix_world @ vertex.co for vertex in meshes[row['id']].data.vertices]
    for axis in range(3):
        for extreme in [min, max]:
            error = abs(extreme(p[axis] for p in points) - extreme(p[axis] for p in row['world_vertices_m'])) * 1000
            assert error < .1, (row['id'], axis, error)
all_points = [ob.matrix_world @ vertex.co for ob in meshes.values() for vertex in ob.data.vertices]
dimensions = [(max(p[i] for p in all_points) - min(p[i] for p in all_points)) * 1000 for i in range(3)]
assert all(abs(value - evidence['dimensions_mm'][key]) < .1 for value, key in zip(dimensions, ['width', 'depth', 'height']))
result = dict(status='PASS', reopened_blend=True, meshes=len(meshes), actual_envelope_mm=dimensions,
              blender_version=bpy.app.version_string, render_executed=False)
(folder / 'blend_reopen_qa.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
