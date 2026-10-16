// HG 3D CLOUD AI - ChatGPT workflow and local 3D editor. No uploads, API keys or persistence.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
const $=id=>document.getElementById(id);
const info=$('cgpt-feedback'),review=$('cgpt-result-note');
let renderer,camera,controls,observer,scene,model,part;
const state={ready:false,origin:null,edited:false};
window.hgChatGPTStudio=state;
function say(message,error=false){info.textContent=message;info.classList.toggle('cgpt-error',error);}
function files(){
 const all=[...($('source-images').files||[])];
 if(all.length&&!$('image-status').textContent.includes('ảnh đang xem trên thiết bị'))throw Error('Đợi website kiểm tra xong ảnh đã chọn.');
 return all.map(f=>({name:f.name.slice(0,180),type:f.type,bytes:f.size}));
}
function job(){
 const images=files(),instruction=$('model-instruction').value.trim().slice(0,4000);
 const known=$('confirmed-measurements').value.trim().slice(0,2000);
 if(!images.length&&instruction.length<12)throw Error('Chọn ảnh hoặc mô tả yêu cầu từ 12 ký tự trở lên.');
 const kind=$('input-type').selectedOptions[0].textContent;
 const prompt=[
 'HG 3D CLOUD AI — YÊU CẦU CHATGPT THIẾT KẾ VÀ CHỈNH SỬA MÔ HÌNH',
 'Đóng vai 18 bộ phận chuyên gia: giám đốc kỹ thuật, kiến trúc, nội thất, họa viên, đo lường, hình học, cấu tạo, thị giác, đa ảnh, vật liệu, UV, ánh sáng, môi trường, camera, tự động hóa và kiểm định.',
 'Nguồn: '+kind+'. Tên ảnh (tôi sẽ tự đính kèm ảnh vào ChatGPT): '+(images.map(f=>f.name).join(', ')||'Không có, yêu cầu bằng văn bản.'),
 'NHIỆM VỤ: '+(instruction||'Phân tích ảnh và tạo bản 3D nháp có thể chỉnh sửa.'),
 'SỐ ĐO ĐÃ XÁC NHẬN (mm): '+(known||'Không có; không được tự đặt kích thước tuyệt đối.'),
 'GIỚI HẠN: không render; không thay kiến trúc hay camera nếu không được yêu cầu. Phân biệt XÁC NHẬN, SUY LUẬN, CẦN XÁC NHẬN. Không phát minh cấu tạo khuất, đường kính lỗ, vật liệu, số đo. Nếu chỉ có một ảnh thiếu tỉ lệ, phải nêu điều thiếu và có thể trả objects=[] thay vì bịa.',
 'KẾT QUẢ: (1) phân tích ngắn và các câu hỏi cần xác nhận; (2) chỉ nếu có đủ bằng chứng kích thước, cung cấp một khối JSON theo cấu trúc ở dưới để tôi dán vào công cụ HG 3D. JSON là bản nháp, không phải file BLEND/GLB đã dựng.',
 'JSON SCHEMA: {"schema":"hg-chatgpt-scene-v1","unit":"mm","review_status":"NEEDS_REVIEW","objects":[{"id":"part_01","name":"Tấm mẫu","shape":"box","size_mm":[1000,450,25],"position_mm":[0,0,500],"rotation_deg":[0,0,0],"color":"#86755f","confidence":"inferred"}],"unknown_details":["Kết cấu khuất chưa xác minh"]}',
 'Đối tượng chỉ dùng shape box hoặc cylinder; size_mm theo [rộng,sâu,cao], position_mm là tọa độ tâm; cylinder có X=Y là đường kính. Không sao chép con số ví dụ nếu không có chứng cứ. Đối tượng không đủ số đo phải được nêu trong unknown_details. Trạng thái luôn NEEDS_REVIEW.'
 ].join('\n\n');
 return {schema:'hg-chatgpt-job-v1',mode:'manual_chatgpt_only',kind:$('input-type').value,instruction,confirmed_measurements_mm:known,
   images,image_bytes_included:false,prompt,notice:'Ảnh KHÔNG nằm trong gói JSON. Người dùng tự đính kèm trong ChatGPT.'};
}
function make(){try{const j=job();$('cgpt-prompt').value=j.prompt;say('Đã tạo yêu cầu. Ảnh vẫn ở thiết bị; đính kèm thủ công trong ChatGPT.');return j;}catch(e){say(e.message,true);return null;}}
async function copy(){const j=make();if(!j)return;try{await navigator.clipboard.writeText(j.prompt);say('Đã sao chép. Chồng mở ChatGPT, dán lệnh và tự đính kèm ảnh.');}catch{$('cgpt-prompt').focus();$('cgpt-prompt').select();say('Đã chọn văn bản, hãy sao chép thủ công.',true);}}
function save(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);}
$('cgpt-generate').addEventListener('click',make);
$('cgpt-copy').addEventListener('click',copy);
$('cgpt-download-job').addEventListener('click',()=>{const j=make();if(j){save(new Blob([JSON.stringify(j,null,2)],{type:'application/json'}),'HG-3D-ChatGPT-job.json');say('Gói JSON đã tải về; không có dữ liệu ảnh bên trong.');}});

const valid=x=>typeof x==='number'&&Number.isFinite(x)&&Math.abs(x)<=100000;
function parseJSON(source){
 if(source.length>256000)throw Error('JSON vượt 256 KB.');
 let s=source.trim(),ticks=String.fromCharCode(96,96,96);
 if(s.startsWith(ticks)){const i=s.indexOf('\n'),end=s.lastIndexOf(ticks);if(i===-1||end<=i)throw Error('Khối JSON chưa đóng.');s=s.slice(i+1,end).trim();}
 const data=JSON.parse(s);
 if(data.schema!=='hg-chatgpt-scene-v1'||data.unit!=='mm'||!Array.isArray(data.objects)||data.objects.length>80)throw Error('Cần schema hg-chatgpt-scene-v1, đơn vị mm và tối đa 80 bộ phận.');
 if(data.unknown_details!==undefined&&(!Array.isArray(data.unknown_details)||data.unknown_details.length>100||!data.unknown_details.every(x=>typeof x==='string'&&x.length<401)))throw Error('Chi tiết cần xác nhận không hợp lệ.');
 const ids=new Set();
 for(const p of data.objects){
  if(!p||typeof p.id!=='string'||!/^[A-Za-z0-9_-]{1,64}$/.test(p.id)||ids.has(p.id))throw Error('ID bộ phận không hợp lệ hoặc trùng nhau.');
  ids.add(p.id);
  if(!['box','cylinder'].includes(p.shape)||!Array.isArray(p.size_mm)||p.size_mm.length!==3||!p.size_mm.every(x=>valid(x)&&x>0)
    ||!Array.isArray(p.position_mm)||p.position_mm.length!==3||!p.position_mm.every(valid)
    ||!Array.isArray(p.rotation_deg)||p.rotation_deg.length!==3||!p.rotation_deg.every(x=>valid(x)&&Math.abs(x)<=3600))
    throw Error('Sai hình học, kích thước, vị trí hoặc góc tại '+p.id);
  if(p.shape==='cylinder'&&Math.abs(p.size_mm[0]-p.size_mm[1])>0.001)throw Error('Đường kính X/Y của cylinder phải bằng nhau.');
  if(p.color!==undefined&&!/^#[a-fA-F0-9]{6}$/.test(p.color))throw Error('Màu phải là #RRGGBB.');
 }
 return data;
}
const world=([x,y,z])=>[x/1000,z/1000,-y/1000];
function groupFromJSON(d){
 if(!d.objects.length)throw Error('Chưa có bộ phận đủ bằng chứng kích thước để dựng 3D.');
 const group=new THREE.Group();group.name='HG_CHATGPT_DRAFT';
 for(const p of d.objects){
  const [w,depth,h]=p.size_mm;
  const geometry=p.shape==='box'?new THREE.BoxGeometry(w/1000,h/1000,depth/1000):new THREE.CylinderGeometry(w/2000,w/2000,h/1000,32);
  const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:p.color||'#948773',roughness:.78,metalness:.1}));
  mesh.name=String(p.name||p.id).slice(0,80);
  mesh.userData.hgId=p.id;mesh.userData.confidence='needs_confirmation';
  mesh.userData.initialScale=[1,1,1];
  mesh.position.set(...world(p.position_mm));
  mesh.rotation.set(-THREE.MathUtils.degToRad(p.rotation_deg[0]),THREE.MathUtils.degToRad(p.rotation_deg[2]),THREE.MathUtils.degToRad(p.rotation_deg[1]));
  group.add(mesh);
 }
 return group;
}
function setup(){
 if(renderer)return;
 scene=new THREE.Scene();scene.background=new THREE.Color('#1b231d');
 scene.add(new THREE.HemisphereLight(0xffffff,0x3c473f,2.4));
 const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(4,6,3);scene.add(light);
 scene.add(new THREE.GridHelper(10,20,0x58664d,0x354339));
 camera=new THREE.PerspectiveCamera(45,1,.001,1000);renderer=new THREE.WebGLRenderer({antialias:true});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
 const target=$('cgpt-viewport');target.replaceChildren(renderer.domElement);
 renderer.domElement.setAttribute('aria-label','Trình xem 3D cục bộ. Kéo để xoay, dùng hai ngón để thu phóng.');
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
 const resize=()=>{const w=Math.max(200,target.clientWidth);camera.aspect=w/360;camera.updateProjectionMatrix();renderer.setSize(w,360,false);};
 resize();observer=new ResizeObserver(resize);observer.observe(target);
 renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
}
function meshes(){const list=[];model?.traverse(x=>{if(x.isMesh)list.push(x);});return list;}
function recenter(){
 if(!model)return;
 model.updateMatrixWorld(true);
 const bb=new THREE.Box3().setFromObject(model);if(bb.isEmpty())return;
 const center=bb.getCenter(new THREE.Vector3()),radius=Math.max(.2,bb.getSize(new THREE.Vector3()).length()/2);
 controls.target.copy(center);camera.near=Math.max(.0001,radius/1000);camera.far=Math.max(100,radius*100);camera.updateProjectionMatrix();
 camera.position.copy(center).add(new THREE.Vector3(radius*2.3,radius*1.7,radius*2.6));controls.update();
}
const fields=['cgpt-x','cgpt-y','cgpt-z','cgpt-rotation','cgpt-scale'];
function fill(){
 if(!part){fields.forEach(id=>$(id).value='');return;}
 $('cgpt-x').value=+(part.position.x*1000).toFixed(2);$('cgpt-y').value=+(-part.position.z*1000).toFixed(2);
 $('cgpt-z').value=+(part.position.y*1000).toFixed(2);
 $('cgpt-rotation').value=+THREE.MathUtils.radToDeg(part.rotation.y).toFixed(2);
 $('cgpt-scale').value=part.userData.hgScalePercent||100;
}
function listParts(){
 const list=meshes(),select=$('cgpt-part');select.replaceChildren();
 list.forEach((m,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=m.name||'Bộ phận '+(i+1);select.append(o);});
 $('cgpt-part-count').textContent=list.length+' bộ phận · BẢN NHÁP';
 part=list[0]||null;fill();state.objects=list.length;
}
function syncMainViewer(){
 try {
  if(model&&window.hgViewer?.showLocalDraft)window.hgViewer.showLocalDraft(model,{
   origin:state.origin||'Bản nháp trên thiết bị',
   unknownDetails:(state.reviewItems||[]).slice(0,30),
   edited:state.edited
  });
 }catch(error){say('Trình xem lớn chưa cập nhật: '+error.message,true);}
}
function show(group,origin,missing=[]){
 setup();if(model)scene.remove(model);model=group;scene.add(group);
 state.ready=true;state.origin=origin;state.edited=false;state.reviewItems=missing;
 listParts();recenter();syncMainViewer();
 review.textContent='CẦN XÁC NHẬN: '+(missing.length?missing.map(s=>String(s).slice(0,180)).join('; '):'Mô hình nháp chưa kiểm tra cấu tạo và kích thước.');
 say('Đang xem 3D cục bộ từ '+origin+'. Không gửi dữ liệu lên máy chủ.');
}
$('cgpt-preview-json').addEventListener('click',()=>{try{const data=parseJSON($('cgpt-scene-json').value);show(groupFromJSON(data),'JSON ChatGPT do người dùng dán',data.unknown_details||[]);}catch(e){say('JSON chưa dựng được: '+e.message,true);}});
$('cgpt-json-file').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>256000)throw Error('JSON vượt 256 KB.');$('cgpt-scene-json').value=await f.text();say('Đã nhập JSON. Bấm Xem 3D từ JSON để tạo bản nháp.');}catch(err){say(err.message,true);}e.target.value='';});
$('cgpt-part').addEventListener('change',()=>{part=meshes()[Number($('cgpt-part').value)]||null;fill();});
$('cgpt-recenter').addEventListener('click',recenter);
$('cgpt-apply').addEventListener('click',()=>{
 if(!part)return say('Chưa chọn bộ phận.',true);
 const values=fields.map(id=>Number($(id).value));
 if(fields.some(id=>$(id).value.trim()==='')||!values.every(Number.isFinite)||values.slice(0,3).some(x=>Math.abs(x)>100000)
    ||Math.abs(values[3])>3600||values[4]<1||values[4]>1000)return say('Vị trí tối đa ±100.000 mm, xoay ±3.600°, tỷ lệ 1–1000%.',true);
 part.position.set(...world(values.slice(0,3)));part.rotation.y=THREE.MathUtils.degToRad(values[3]);
 if(!part.userData.initialScale)part.userData.initialScale=part.scale.toArray();
 part.scale.fromArray(part.userData.initialScale).multiplyScalar(values[4]/100);
 part.userData.hgScalePercent=values[4];state.edited=true;syncMainViewer();
 review.textContent='ĐÃ CHỈNH CỤC BỘ · CẦN XÁC NHẬN vị trí, va chạm, kích thước thực và cấu tạo.';
 say('Đã chỉnh bộ phận trong trình duyệt; chưa lưu lên server.');
});
$('cgpt-remove-part').addEventListener('click',()=>{
 if(!part||!part.parent)return say('Chưa có bộ phận cần bỏ.',true);
 part.parent.remove(part);state.edited=true;listParts();recenter();syncMainViewer();
 review.textContent='ĐÃ BỎ BỘ PHẬN · CẦN XÁC NHẬN';say('Đã xóa bộ phận khỏi bản nháp cục bộ.');
});
$('cgpt-glb-file').addEventListener('change',async e=>{
 const f=e.target.files[0];if(!f)return;
 try{
  if(!f.size||f.size>30*1024*1024)throw Error('GLB phải nhỏ hơn 30 MB.');
  const b=await f.arrayBuffer(),v=new DataView(b);
  if(b.byteLength<20||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==b.byteLength||v.getUint32(16,true)!==0x4e4f534a)throw Error('GLB 2.0 không hợp lệ.');
  const length=v.getUint32(12,true);if(length<2||20+length>b.byteLength)throw Error('JSON chunk GLB bị hỏng.');
  const json=JSON.parse(new TextDecoder().decode(b.slice(20,20+length)).trim());
  if([...(json.images||[]),...(json.buffers||[])].some(x=>x.uri))throw Error('GLB có liên kết tài nguyên ngoài, đã chặn.');
  const gltf=await new GLTFLoader().parseAsync(b,'');
  const group=new THREE.Group();group.name='HG_IMPORTED_GLB';group.add(gltf.scene);
  show(group,'GLB người dùng tải lên',['Chưa kiểm định mô hình nhập']);
 }catch(err){say('Mở GLB không thành công: '+err.message,true);}
 e.target.value='';
});
$('cgpt-export-glb').addEventListener('click',async()=>{
 if(!model||!meshes().length)return say('Chưa có mô hình để xuất.',true);
 const button=$('cgpt-export-glb');button.disabled=true;
 try{
  const data=await new GLTFExporter().parseAsync(model,{binary:true,onlyVisible:true,maxTextureSize:2048});
  if(!(data instanceof ArrayBuffer))throw Error('Chưa xuất được GLB nhị phân.');
  save(new Blob([data],{type:'model/gltf-binary'}),'HG-3D-DRAFT-NEEDS-REVIEW.glb');
  say('Đã tải GLB NHÁP. Đây không phải BLEND hoặc mô hình đã nghiệm thu.');
 }catch(e){say('Không xuất được GLB: '+e.message,true);}
 finally{button.disabled=false;}
});
$('cgpt-export-fbx').addEventListener('click',async()=>{
 if(!model||!meshes().length)return say('Chưa có mô hình để xuất FBX.',true);
 const button=$('cgpt-export-fbx');button.disabled=true;
 try {
  const {FBXExporter}=await import('@comfyorg/fbx-exporter-three');
  const bytes=await new FBXExporter().parseAsync(model,{preset:'blender',onlyVisible:true,includeAnimations:false,embedTextures:true});
  if(!(bytes instanceof Uint8Array)||bytes.byteLength<128||
     !new TextDecoder().decode(bytes.subarray(0,18)).startsWith('Kaydara FBX Binary')){
   throw Error('Thư viện chưa xuất được FBX nhị phân hợp lệ.');
  }
  save(new Blob([bytes],{type:'application/octet-stream'}),'HG-3D-DRAFT-NEEDS-REVIEW.fbx');
  say('Đã tải FBX nhị phân NHÁP. Chưa được kiểm định trong phần mềm đích.');
 }catch(error){say('Không xuất được FBX: '+error.message,true);}
 finally{button.disabled=false;}
});

window.addEventListener('pagehide',()=>{renderer?.setAnimationLoop(null);controls?.dispose();observer?.disconnect();renderer?.dispose();});
say('Sẵn sàng tạo lệnh cho ChatGPT. Ảnh chưa được gửi đi.');
