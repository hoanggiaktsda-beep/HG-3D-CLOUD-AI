"""Blender-only TEST33 inventory: actual mesh/material/light/camera/collection values.
Does not render, change the source scene, or grant final design approval.
"""
import bpy,json,sys,math,bmesh
from pathlib import Path
source,folder,output=map(Path,sys.argv[sys.argv.index('--')+1:])
spec=json.loads(source.read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder/'hg_scene.blend'))
bpy.context.view_layer.update()
meshes=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data)
 meshes.append({'id':ob.name,'source_id':ob.get('HG_source_id'),'confidence':ob.get('HG_confidence'),
  'collections':[c.name for c in ob.users_collection],'material_slots':[m.name for m in ob.data.materials],
  'vertices':len(bm.verts),'manifold':all(e.is_manifold for e in bm.edges),'volume_m3':abs(bm.calc_volume()),
  'uv_layers':list(ob.data.uv_layers.keys())})
 bm.free()
assert meshes and all(m['manifold'] and m['volume_m3']>0 and m['material_slots'] and m['collections'] for m in meshes)
materials=[]
for m in bpy.data.materials:
 if not m.users:continue
 bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
 assert bs is not None
 materials.append({'id':m.name,'base_color':list(bs.inputs['Base Color'].default_value),
  'roughness':bs.inputs['Roughness'].default_value,'metallic':bs.inputs['Metallic'].default_value})
lights=[]
for item in spec.get('lights',[]):
 ob=bpy.data.objects[item['id']];assert ob.type=='LIGHT' and ob.data.type=='AREA'
 assert abs(ob.data.energy-item['power_w'])<.001
 assert abs(ob.data.size*1000-item.get('diameter_mm',600))<.01
 assert all(abs(ob.location[i]*1000-item['position_mm'][i])<.01 for i in range(3))
 lights.append({'id':ob.name,'type':ob.data.type,'power_w':ob.data.energy,'size_mm':ob.data.size*1000})
cameras=[]
from mathutils import Vector
for item in spec.get('cameras',[]):
 ob=bpy.data.objects[item['id']];assert ob.type=='CAMERA'
 assert abs(ob.data.lens-item.get('lens_mm',35))<.001
 aim=(Vector(item['target_mm'])*.001-ob.location).normalized()
 actual=ob.rotation_euler.to_matrix()@Vector((0,0,-1))
 assert aim.dot(actual)>.999999
 cameras.append({'id':ob.name,'lens_mm':ob.data.lens,'direction_dot':aim.dot(actual)})
world={'present':bpy.context.scene.world is not None,'source_environment_specified':False,'verified_against_photo':False}
blend={'meshes':meshes,'materials':materials,'lights':lights,'cameras':cameras,'world':world,'active_camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(folder/'hg_scene.glb'))
interchange={'meshes':sum(o.type=='MESH' for o in bpy.context.scene.objects),
 'cameras':[{'id':o.name,'lens_mm':o.data.lens} for o in bpy.context.scene.objects if o.type=='CAMERA'],
 'lights':[{'id':o.name,'type':o.data.type} for o in bpy.context.scene.objects if o.type=='LIGHT'],
 'collections':[c.name for c in bpy.data.collections],
 'limits':['GLB does not guarantee Blender collection/layer semantics or area-light fidelity; measured inventory only.']}
result={'status':'TECHNICAL_SAMPLE_CHECKED_NOT_FINAL_APPROVAL','blend':blend,'glb':interchange,
 'render_executed':False,'automatic_vision_executed':False,'test30_status':'CẦN XÁC NHẬN',
 'limits':['Basic PBR values are not verified product materials, UV quality or photo matching.',
 'No source environment, HDRI or photographic lighting reference was supplied.',
 'Closed basic meshes do not establish joinery, collision-free assembly or manufacturing readiness.']}
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'meshes':len(meshes),'materials':len(materials),'lights':lights,'cameras':cameras,'glb':interchange},ensure_ascii=False))
