"""Executed by real Blender: blender -b --python scripts/blender_build.py -- scene.json output_dir
Produces .blend + .glb (if glTF add-on exists). NEVER calls renderer.
Geometry is deliberately approximate for complex furniture until reference data is verified.
"""
from __future__ import annotations
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from hgcloud.core import load,save_report
from hgcloud.preview import build_html

if '--' not in sys.argv or len(sys.argv[sys.argv.index('--')+1:])!=2:
    raise SystemExit('Cách chạy: blender -b --python scripts/blender_build.py -- examples/living_room.json outputs/demo')
sp, out = sys.argv[sys.argv.index('--')+1:]
scene=load(sp)
out=Path(out).expanduser().resolve()
if out.exists() and any(out.iterdir()):
    raise SystemExit('Từ chối ghi đè output đã có: '+str(out))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for old in list(bpy.data.collections):
    if old.name != bpy.context.scene.collection.name and old.users==0:
        bpy.data.collections.remove(old)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
bpy.context.scene.unit_settings.length_unit='MILLIMETERS'
MM=0.001
palette={'default':(0.63,0.64,0.65),'wood':(0.26,0.15,0.08),'stone':(0.71,0.70,0.66),'fabric':(0.59,0.56,0.51),'leather':(0.23,0.20,0.18),'metal':(0.30,0.32,0.35),'glass':(0.70,0.78,0.82),'plaster':(0.88,0.86,0.82),'paint':(0.83,0.82,0.78),'concrete':(0.55,0.55,0.52),'carpet':(0.47,0.43,0.40)}
mat_cache={}

def mat(name,color=None):
    rgb=tuple(color or palette.get(name,palette['default']))
    key=(name,rgb)
    if key in mat_cache:return mat_cache[key]
    m=bpy.data.materials.new('HG_'+name)
    m.diffuse_color=(*rgb,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=(*rgb,1)
        bs.inputs['Roughness'].default_value=0.4 if name in {'metal','stone'} else 0.72
        if name=='metal':bs.inputs['Metallic'].default_value=0.8
    mat_cache[key]=m
    return m

def collection(name):
    c=bpy.data.collections.get(name)
    if not c:
        c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
    return c

def organize(obj,coll):
    for old in list(obj.users_collection):old.objects.unlink(obj)
    coll.objects.link(obj)

def cuboid(name,center,size,material,coll,color=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[v*MM for v in center])
    ob=bpy.context.object;ob.name=name
    ob.dimensions=[v*MM for v in size]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat(material,color));organize(ob,coll)
    return ob

def cylinder(name,center,size,material,coll,color=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.5,depth=1,location=[v*MM for v in center])
    ob=bpy.context.object;ob.name=name;ob.dimensions=[v*MM for v in size]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat(material,color));organize(ob,coll)
    return ob

def build(o):
    kind=o['kind'];c=list(o['center_mm']);s=list(o['size_mm']);m=o.get('material','default');color=o.get('color_rgb')
    coll=collection('HG_'+('ARCH' if kind in {'wall','floor','ceiling','window','door','column'} else 'FURNITURE'))
    parts=[]
    def add_box(tag,point,dims,material=m):parts.append(cuboid(o['id']+'_'+tag,point,dims,material,coll,color if material==m else None))
    if kind in {'box','wall','floor','ceiling','door','window','panel','shelf','rug','column'}:
        add_box('body',c,s)
    elif kind=='cylinder':parts.append(cylinder(o['id']+'_body',c,s,m,coll,color))
    elif kind=='sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=0.5,location=[v*MM for v in c]);ob=bpy.context.object
        ob.name=o['id']+'_body';ob.dimensions=[v*MM for v in s];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        ob.data.materials.append(mat(m,color));organize(ob,coll);parts.append(ob)
    elif kind in {'sofa','armchair'}:
        x,y,z=s
        # All parts stay within the overall bounding box; back at positive Y.
        seat_h=min(z*0.48,470); base_h=seat_h*0.65;back_h=z-seat_h
        # Seat front and backrest rear anchor the design depth at +/- y/2.
        add_box('seat',[c[0],c[1]-y*0.11,c[2]-z/2+seat_h*0.85],[x*.91,y*.78,seat_h*.34])
        add_box('base',[c[0],c[1],c[2]-z/2+base_h/2],[x*.92,y*.88,base_h])
        add_box('back',[c[0],c[1]+y*.40,c[2]+z/2-back_h/2],[x,y*.20,back_h])
        arm_w=min(150,x*.12); arm_h=min(300,z*.50)
        for side,sign in [('left',-1),('right',1)]:
            add_box('arm_'+side,[c[0]+sign*(x/2-arm_w/2),c[1],c[2]-z/2+seat_h+arm_h/2],[arm_w,y*.76,arm_h])
    elif kind=='coffee_table':
        x,y,z=s;top=max(18,min(z*.12,55));leg=max(30,min(x,y)*.08)
        add_box('top',[c[0],c[1],c[2]+z/2-top/2],[x,y,top])
        for i,dx in enumerate((-1,1)):
            for j,dy in enumerate((-1,1)):
                add_box('leg_%s%s'%(i,j),[c[0]+dx*(x/2-leg),c[1]+dy*(y/2-leg),c[2]-top/2],[leg,leg,z-top], 'metal')
    elif kind=='cabinet':
        x,y,z=s;t=min(max(x*.025,12),30)
        add_box('bottom',[c[0],c[1],c[2]-z/2+t/2],[x,y,t])
        add_box('top',[c[0],c[1],c[2]+z/2-t/2],[x,y,t])
        for sign in (-1,1):add_box('side_'+str(sign),[c[0]+sign*(x/2-t/2),c[1],c[2]],[t,y,z])
        add_box('back',[c[0],c[1]+y/2-t/2,c[2]],[x,t,z])
        add_box('door_L',[c[0]-x/4,c[1]-y/2+t/2,c[2]],[x/2-t/2,t,z-2*t])
        add_box('door_R',[c[0]+x/4,c[1]-y/2+t/2,c[2]],[x/2-t/2,t,z-2*t])
    elif kind=='bed':
        x,y,z=s;frame_h=z*.32
        add_box('frame',[c[0],c[1],c[2]-z/2+frame_h/2],[x,y,frame_h],'wood')
        add_box('mattress',[c[0],c[1]-y*.045,c[2]-z/2+frame_h+z*.09],[x*.95,y*.84,z*.18],'fabric')
        add_box('headboard',[c[0],c[1]+y*.45,c[2]+z*.12],[x,y*.11,z*.76],'fabric')
    else:raise ValueError('Unsupported '+kind)
    # IMPORTANT rotations can be applied per part about common center, not each local center.
    if o.get('rotation_deg'):
        from mathutils import Matrix,Euler
        pivot=Vector([v*MM for v in c]);rot=Euler(tuple(math.radians(v) for v in o['rotation_deg']),'XYZ').to_matrix()
        for ob in parts:
            ob.location=pivot+rot@(ob.location-pivot)
            ob.rotation_euler=tuple(math.radians(v) for v in o['rotation_deg'])
    for ob in parts:
        ob['HG_source_id']=o['id'];ob['HG_confidence']=o['confidence'];ob['HG_source_note']=o.get('source_note','')
        ob['HG_design_size_mm']=json.dumps(s)
    return parts

all_created=[]
for o in scene['objects']:
    all_created += build(o)

for l in scene.get('lights',[]):
    data=bpy.data.lights.new(l['id'],'AREA');data.energy=l['power_w'];data.shape='DISK';data.size=l.get('diameter_mm',600)*MM
    ob=bpy.data.objects.new(l['id'],data);collection('HG_LIGHTS').objects.link(ob)
    ob.location=[v*MM for v in l['position_mm']]

for c in scene.get('cameras',[]):
    data=bpy.data.cameras.new(c['id']);ob=bpy.data.objects.new(c['id'],data)
    collection('HG_CAMERAS').objects.link(ob)
    ob.location=Vector([v*MM for v in c['position_mm']]);target=Vector([v*MM for v in c['target_mm']])
    direction=target-ob.location
    if direction.length>1e-5:ob.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    data.lens=c.get('lens_mm',35)
    if bpy.context.scene.camera is None:bpy.context.scene.camera=ob

# DO NOT render; only save editable scene and interchange model.
blend=out/'hg_scene.blend';glb=out/'hg_scene.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
export_error=None
try:
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_cameras=True,export_lights=True)
except Exception as exc:
    export_error=str(exc)
report=save_report(scene,out/'qa_report.json')
report['evidence']['actual_geometry_export_tested']=export_error is None and glb.exists()
report['blender_details']={'blend_created':blend.exists(),'glb_created':glb.exists(),'objects_in_scene':len(all_created),'glb_error':export_error,
                           'viewport_measurement_completed':False,'render_executed':False}
(out/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
build_html(out/'qa_report.json',out/'qa_report.html')
print('HG3D: BLEND',blend,'GLB',glb if glb.exists() else 'failed; see qa_report.json')
