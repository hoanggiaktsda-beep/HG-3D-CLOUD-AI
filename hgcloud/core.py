"""Validated scene contracts, deterministic QA and job isolation. No third-party dependencies."""
from __future__ import annotations
import json, math, re
from pathlib import Path
from datetime import datetime, timezone

KINDS = {'box','cylinder','sphere','sofa','armchair','coffee_table','cabinet','bed','wall','floor','ceiling','door','window','panel','shelf','rug','column'}
STATES = {'confirmed','inferred','needs_confirmation'}
MATERIALS = {'default','wood','stone','fabric','leather','metal','glass','plaster','paint','concrete','carpet'}
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')

class SceneError(ValueError):
    pass

def require(cond, msg):
    if not cond: raise SceneError(msg)

def vec3(value, key, *, positive=False):
    require(isinstance(value,list) and len(value)==3, f'{key}: cần mảng 3 số')
    require(all(type(v) in (int,float) and math.isfinite(v) for v in value), f'{key}: cần 3 số hữu hạn')
    if positive: require(all(v>0 for v in value), f'{key}: kích thước phải > 0')
    return value

def validate(scene):
    require(isinstance(scene,dict), 'scene phải là JSON object')
    require(scene.get('schema_version')=='1.0', 'schema_version phải là 1.0')
    require(scene.get('units')=='mm', 'đơn vị bắt buộc mm')
    require(isinstance(scene.get('project'),str) and bool(scene['project'].strip()), 'thiếu tên project')
    objs=scene.get('objects')
    require(isinstance(objs,list) and len(objs)>0, 'objects phải là mảng có phần tử')
    seen=set()
    for i,o in enumerate(objs):
        k=f'objects[{i}]'
        require(isinstance(o,dict), f'{k} phải là object')
        ident=o.get('id')
        require(isinstance(ident,str) and ID_RE.fullmatch(ident) is not None, f'{k}.id sai định dạng')
        require(ident not in seen, f'trùng id: {ident}')
        seen.add(ident)
        require(o.get('kind') in KINDS, f'{ident}: loại hình học chưa hỗ trợ {o.get("kind")}')
        vec3(o.get('center_mm'),f'{ident}.center_mm')
        vec3(o.get('size_mm'),f'{ident}.size_mm',positive=True)
        require(o.get('confidence') in STATES, f'{ident}: thiếu confidence')
        require(o.get('material','default') in MATERIALS, f'{ident}: vật liệu không hỗ trợ')
        rot=o.get('rotation_deg',[0,0,0]); vec3(rot,f'{ident}.rotation_deg')
        require(isinstance(o.get('source_note',''),str),f'{ident}: source_note sai')
        if o['confidence']=='confirmed':
            require(bool(o.get('source_note','').strip()),f'{ident}: đã xác nhận phải có nguồn bằng chứng')
        for optional in ('color_rgb','dimensions_tolerance_mm'):
            if optional in o:
                if optional=='color_rgb':
                    c=o[optional]; require(isinstance(c,list) and len(c)==3 and all(type(v) in (int,float) and 0<=v<=1 for v in c), f'{ident}: color_rgb yêu cầu 0..1')
                else:
                    v=o[optional]; require(type(v) in (int,float) and math.isfinite(v) and v>=0,f'{ident}: tolerance không hợp lệ')
    lights=scene.get('lights',[]); require(isinstance(lights,list),'lights phải là mảng')
    for l in lights:
        require(isinstance(l,dict) and isinstance(l.get('id'),str),'đèn cần id')
        vec3(l.get('position_mm'),f'light {l["id"]}')
        require(type(l.get('power_w')) in (int,float) and 0<=l['power_w']<=100000, 'power_w không hợp lệ')
    cams=scene.get('cameras',[]); require(isinstance(cams,list),'cameras phải là mảng')
    for c in cams:
        require(isinstance(c,dict) and isinstance(c.get('id'),str),'camera cần id')
        vec3(c.get('position_mm'),f'camera {c["id"]}')
        vec3(c.get('target_mm'),f'camera target {c["id"]}')
    return scene

def load(path):
    scene=json.loads(Path(path).read_text(encoding='utf-8'))
    return validate(scene)

def audit(scene):
    validate(scene)
    objs=scene['objects']; review=[]; warnings=[]; checks=[]
    for o in objs:
        if o['confidence']!='confirmed':
            review.append({'id':o['id'],'status':o['confidence'],'reason':o.get('source_note','Không có nguồn đo trực tiếp')})
        sx,sy,sz=o['size_mm']
        if max(sx,sy,sz)/min(sx,sy,sz)>1000:
            warnings.append(f'{o["id"]}: tỷ lệ rất lớn; kiểm tra đơn vị hoặc chiều dày')
        if o['kind'] in {'sofa','armchair','bed','coffee_table','cabinet'}:
            checks.append({'object_id':o['id'],'geometry':'bounding-box + basic parametric parts','manufacturing_ready':False})
    status='NEEDS_REVIEW' if review else 'SPEC_VALIDATED'
    return {'project':scene['project'],'status':status,'objects':len(objs),
            'confirmed':sum(o['confidence']=='confirmed' for o in objs),
            'inferred':sum(o['confidence']=='inferred' for o in objs),
            'needs_confirmation':sum(o['confidence']=='needs_confirmation' for o in objs),
            'review_items':review,'warnings':warnings,'checks':checks,
            'evidence':{'measured_dimensions_from_blender':False,'image_similarity_verified':False,'actual_geometry_export_tested':False},
            'limits':['Kiểm tra JSON không xác nhận kích thước hình học trong file BLEND.',
                      'Ảnh đơn lẻ không cho phép xác minh chi tiết khuất hoặc đạt độ giống 100%.',
                      'Scene tham số chỉ là điểm xuất phát; không phải hồ sơ CNC / shop drawing.',
                      'Chỉ được nghiệm thu kỹ thuật sau khi đo lại file xuất và so với dữ liệu gốc.']}

def save_report(scene,output):
    p=Path(output); p.parent.mkdir(parents=True,exist_ok=True)
    payload=audit(scene); payload['generated_utc']=datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return payload
