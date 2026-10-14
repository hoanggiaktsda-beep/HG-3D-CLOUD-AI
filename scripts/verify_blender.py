"""Run with Blender: independent evaluated mesh measurement, never renders."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Euler
scene_path,build_path=map(Path,sys.argv[sys.argv.index('--')+1:])
scene=json.loads(scene_path.read_text());out=build_path
bpy.ops.wm.open_mainfile(filepath=str(out/'hg_scene.blend'))
rows=[];deps=bpy.context.evaluated_depsgraph_get()
for spec in scene['objects']:
    parts=[o for o in bpy.data.objects if o.type=='MESH' and o.get('HG_source_id')==spec['id']]
    points=[]
    inv=Euler(tuple(math.radians(v) for v in spec.get('rotation_deg',[0,0,0])),'XYZ').to_matrix().inverted()
    center=Vector(spec['center_mm'])*.001
    for obj in parts:
        evaluated=obj.evaluated_get(deps)
        points.extend(inv@(evaluated.matrix_world@v.co-center) for v in evaluated.data.vertices)
    tolerance=spec.get('dimensions_tolerance_mm',1)
    actual=[(max(p[i] for p in points)-min(p[i] for p in points))*1000 for i in range(3)] if points else None
    errors=[actual[i]-spec['size_mm'][i] for i in range(3)] if actual else None
    center_errors=[(max(p[i] for p in points)+min(p[i] for p in points))*500 for i in range(3)] if points else None
    rows.append({'id':spec['id'],'expected_mm':spec['size_mm'],'actual_mm':actual,'error_mm':errors,
                 'center_error_mm':center_errors,'tolerance_mm':tolerance,
                 'pass':bool(points) and all(abs(v)<=tolerance for v in errors+center_errors),
                 'dimension_evidence':spec.get('dimension_evidence',{}),
                 'unknown_details':spec.get('unknown_details',[])})
report=json.loads((out/'qa_report.json').read_text())
report['geometry_measurements']=rows
report['evidence']['measured_dimensions_from_blender']=True
report['geometry_status']='PASS' if all(r['pass'] for r in rows) else 'QA_FAILED'
if report['geometry_status']=='QA_FAILED': report['status']='QA_FAILED'
if any(r['unknown_details'] for r in rows):
    if report['status']!='QA_FAILED':report['status']='NEEDS_REVIEW'
    report['limits'].append('Unknown construction details remain; envelope only, not manufacturing geometry.')
(out/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hgcloud.preview import build_html
build_html(out/'qa_report.json',out/'qa_report.html')
print(json.dumps(rows,indent=2))
if report['geometry_status']=='QA_FAILED':raise RuntimeError('Geometry deviation exceeds tolerance')
