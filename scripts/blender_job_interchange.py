"""Real BLEND reopen / GLB reimport for TEST 31 public jobs. No rendering."""
import bpy
import json
from pathlib import Path
import sys
from mathutils.kdtree import KDTree

folder = Path(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=str((folder / 'hg_scene.blend').resolve()))
source = {o.name: [tuple(o.matrix_world @ v.co) for v in o.data.vertices] for o in bpy.data.objects if o.type == 'MESH'}
assert source
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str((folder / 'hg_scene.glb').resolve()))
imported = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
assert set(imported) == set(source), 'GLB part inventory changed'
rows = []
for name, original in source.items():
    actual = [tuple(imported[name].matrix_world @ v.co) for v in imported[name].data.vertices]
    error = 0
    for a, b in [(original, actual), (actual, original)]:
        tree = KDTree(len(b))
        for i, p in enumerate(b): tree.insert(p, i)
        tree.balance()
        error = max(error, max(tree.find(p)[2] * 1000 for p in a))
    assert error < .1, (name, error)
    rows.append(dict(id=name, bidirectional_vertex_error_mm=error))
(folder / 'interchange_qa.json').write_text(json.dumps(dict(status='PASS', blend_reopen=True,
    glb_reimport=True, objects=rows, render_executed=False), indent=2))
