"""Repackage only the reviewed public GLB as an editable BLEND; never render."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
source=root/'viewer/assets/sample.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='67f0f3a96927570782d8fcb596e32a904dcfd0ca9cce70f39e99cb2121368ff3'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
def audit():
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    dims=[(max(v[i] for v in points)-min(v[i] for v in points))*1000 for i in range(3)]
    assert len(meshes)==8
    assert all(abs(a-b)<.01 for a,b in zip(dims,[1800,450,850])),dims
    assert not bpy.data.images
    return {'mesh_count':len(meshes),'measured_mm':dims,'status':'CẦN XÁC NHẬN','source':'reviewed public sample.glb; editable imported meshes, not original parametric scene','rendered':False}
report=audit()
bpy.context.scene['review_status']='NEEDS_CONFIRMATION'
bpy.ops.wm.save_as_mainfile(filepath=str(root/'viewer/assets/sample.blend'))
bpy.ops.wm.open_mainfile(filepath=str(root/'viewer/assets/sample.blend'))
assert audit()==report
(root/'outputs/test32/blend-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
