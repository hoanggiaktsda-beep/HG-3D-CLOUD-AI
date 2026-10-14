"""Build evidence-traced plate profiles. Blender only; no rendering."""
import bpy,bmesh,json,math,sys,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
evidence=json.loads(source.read_text())
assert hashlib.sha256(Path(evidence['source']).read_bytes()).hexdigest()==evidence['sha256'],'Source image changed'
out.mkdir(parents=True,exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.length_unit='MILLIMETERS'
d=evidence['dimensions_mm'];w,t,h=[d[k]/1000 for k in ['width','thickness','height']]
mat=bpy.data.materials.new('Evidence plywood');mat.diffuse_color=(.62,.43,.24,1)
parts=[];markers=[];specs={}

def extrude(name,poly,thickness,plane='xz'):
    verts=[(x,offset,z) if plane=='xz' else (x,z,offset) for offset in [-thickness/2,thickness/2] for x,z in poly]
    n=len(poly);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat)
    return ob

def mapping(profile,kind):
    pts=profile['outline_px'];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
    if kind=='side':
        return lambda p:((max(xs)-p[0])/(max(xs)-min(xs))*(w-t)-(w-t)/2,(p[1]-min(ys))/(max(ys)-min(ys))*(h-t))
    return lambda p:((p[0]-(max(xs)+min(xs))/2)/(max(xs)-min(xs))*w,(p[1]-(max(ys)+min(ys))/2)/(max(ys)-min(ys))*w)

for name,profile in evidence['profiles'].items():
    convert=mapping(profile,name)
    poly=[convert(p) for p in profile['outline_px']]
    copies=4 if name=='side' else 1
    for i in range(copies):
        ident='panel_'+str(i) if name=='side' else 'seat'
        ob=extrude(ident,poly,t,'xz' if name=='side' else 'xy')
        matrix=(Matrix.Rotation(math.pi*i/2,4,'Z')@Matrix.Translation(Vector((0,-(w-t)/2,0)))) if name=='side' else Matrix.Translation(Vector((0,0,h-t/2)))
        ob.matrix_world=matrix
        for index,hole in enumerate(profile['voids_px']):
            cutter=extrude('temporary_void',[convert(p) for p in hole],t*3,'xz' if name=='side' else 'xy');cutter.matrix_world=matrix
            bpy.context.view_layer.objects.active=ob
            modifier=ob.modifiers.new('image_observed_void','BOOLEAN');modifier.operation='DIFFERENCE';modifier.object=cutter;modifier.solver='EXACT'
            bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
        ob['source_sha256']=evidence['sha256'];ob['confidence']='inferred';ob['review']='CẦN XÁC NHẬN: raster contour, tolerances and relief radii'
        parts.append(ob)
        specs[ident]={'expected_local_mm':[1000*(w-t),1000*t,1000*(h-t)] if name=='side' else [1000*w,1000*w,1000*t],
                      'expected_matrix':[list(row) for row in matrix],'outline_vertices':len(poly),'profile_name':name}
        for j,marker in enumerate(profile['drill_markers']):
            a,b=convert(marker['center_px'])
            position=Vector((a,-t/2-.001,b)) if name=='side' else Vector((a,b,t/2+.001))
            empty=bpy.data.objects.new(ident+'_drill_'+str(j)+'_NEEDS_CONFIRMATION',None);bpy.context.collection.objects.link(empty)
            empty.empty_display_type='PLAIN_AXES';empty.empty_display_size=.007;empty.location=matrix@position
            empty['diameter_mm']='UNKNOWN';empty['feature']='Observed drill symbol, no bore cut';empty['review']='CẦN XÁC NHẬN'
            markers.append(empty)
bpy.context.view_layer.update()
rows=[]
for ob in parts:
    bm=bmesh.new();bm.from_mesh(ob.data)
    sizes=[(max(v.co[i] for v in bm.verts)-min(v.co[i] for v in bm.verts))*1000 for i in range(3)]
    expected=specs[ob.name]['expected_local_mm']
    dim_errors=[a-b for a,b in zip(sizes,expected)]
    transform_error=max(abs(ob.matrix_world[i][j]-specs[ob.name]['expected_matrix'][i][j]) for i in range(4) for j in range(4))
    bad_edges=sum(not e.is_manifold for e in bm.edges);volume=abs(bm.calc_volume(signed=True))*1e9
    degenerate_faces=sum(f.calc_area()<1e-14 for f in bm.faces)
    shortest=min(e.calc_length() for e in bm.edges)*1000
    points=[list(ob.matrix_world@v.co) for v in bm.verts]
    bmesh.ops.triangulate(bm,faces=list(bm.faces));tree=BVHTree.FromBMesh(bm)
    if ob.name=='seat':
        hole=evidence['profiles']['seat']['voids_px'][0];convert=mapping(evidence['profiles']['seat'],'seat')
        cp=convert([sum(p[0] for p in hole)/len(hole),sum(p[1] for p in hole)/len(hole)])
        hit=tree.ray_cast(Vector((cp[0],cp[1],t*2)),Vector((0,0,-1)),t*4)[0]
        assert hit is None,'Observed central void was filled'
    passed=all(abs(e)<.1 for e in dim_errors) and transform_error<1e-6 and bad_edges==0 and volume>0 and degenerate_faces==0
    rows.append({'id':ob.name,'actual_local_mm':sizes,'expected_local_mm':expected,'errors_mm':dim_errors,
                 'world_center_mm':[v*1000 for v in ob.location],'transform_error':transform_error,
                 'nonmanifold_edges':bad_edges,'degenerate_faces':degenerate_faces,'volume_mm3':volume,
                 'shortest_mesh_edge_mm':shortest,'source_outline_vertices':specs[ob.name]['outline_vertices'],
                 'pass':passed,'confidence':'inferred','review':'CẦN XÁC NHẬN source dimensions of detail and fitting clearance',
                 'world_vertices_m':points})
    bm.free()
assert all(r['pass'] for r in rows),[(r['id'],r['pass']) for r in rows]
expected_markers=4*len(evidence['profiles']['side']['drill_markers'])+len(evidence['profiles']['seat']['drill_markers'])
assert len(markers)==expected_markers and all(m['diameter_mm']=='UNKNOWN' for m in markers)
assert all(abs(p.location.length-(w-t)/2)<1e-6 for p in parts if p.name.startswith('panel_'))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'detailed_draft.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'detailed_draft.glb').resolve()),export_format='GLB',export_extras=True)
report={'status':'NEEDS_REVIEW','objects':rows,'drill_markers':len(markers),'physical_drill_bores':0,
 'central_void_test':'PASS ray through void misses material','render_executed':False,
 'unknown':['Drill diameters','Cutter radius','Exact dogbone radius','Fitting clearances','Original CNC geometry'],
 'thin_geometry':'Plate thickness verified per object; smallest edges report raster segmentation, not engineering minimum ligaments',
 'source_uncertainty':'1 pixel quantization, nominal detail scale; no sub-mm source precision claim'}
(out/'object_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str((out/'detailed_draft.glb').resolve()))
imported={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert set(imported)=={r['id'] for r in rows}
for row in rows:
    ob=imported[row['id']]
    points=[ob.matrix_world@v.co for v in ob.data.vertices]
    expected_points=row['world_vertices_m']
    errors=[abs(max(p[i] for p in points)-max(p[i] for p in expected_points))*1000 for i in range(3)]+[abs(min(p[i] for p in points)-min(p[i] for p in expected_points))*1000 for i in range(3)]
    assert max(errors)<.1,(ob.name,errors)
imported_markers=[o for o in bpy.data.objects if o.type=='EMPTY' and '_drill_' in o.name]
assert len(imported_markers)==expected_markers and all(o.get('diameter_mm')=='UNKNOWN' for o in imported_markers)
report['glb_drill_markers']=len(imported_markers)
report['glb_object_checks']='PASS five mesh objects reimported, world bbox per object within 0.1 mm'
(out/'object_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASS per-object dimensions, transforms, manifold, central opening and GLB reimport')
